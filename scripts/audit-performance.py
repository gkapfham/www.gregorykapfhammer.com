"""Measure the performance of a locally built site with Lighthouse.

This is a development tool, not part of the publishing workflow. The publish
workflow in .github/workflows/publish.yml is unchanged and does not call this
script.

Why this script exists
----------------------
`quarto preview` is a development server. It serves the unminified sources,
skips every post-render optimization (CSS purging, JavaScript deferral,
resource preloading), and injects its own preview client, which is extra
JavaScript and extra DOM. A Lighthouse run against the preview server
therefore measures a build that will never be deployed, and it reports scores
that are much lower than the deployed site.

This script measures the build that the publish workflow produces:

1. Build with `scripts/build-local.py`, which mirrors the GitHub Actions
   workflow (render, then the same optimizations in the same order).
2. Serve the resulting `_site` directory from a local HTTP server that
   compresses text responses with gzip, the way Cloudflare serves the deployed
   site with Brotli.
3. Run Lighthouse against that server for each requested device.
4. Optionally run the same audits against a deployed URL, so that the local
   build can be compared with the site that is currently live.

Usage
-----
    # Build, then measure the home page on desktop and mobile
    uv run python scripts/audit-performance.py

    # Reuse the existing _site directory instead of rebuilding
    uv run python scripts/audit-performance.py --skip-build

    # Compare the local build with the deployed site
    uv run python scripts/audit-performance.py \
        --baseline https://www.gregorykapfhammer.com

    # Several pages, three runs each, mobile only
    uv run python scripts/audit-performance.py --runs 3 --device mobile \
        --pages / /blog/ /research/papers/

Lighthouse reports are written to `_audit/` so that they can be opened in a
browser. Lighthouse itself reports a cold-cache, first-visit experience with
simulated network throttling, so repeated runs still vary by several points;
use `--runs` and read the reported range, not a single number.
"""

import argparse
import gzip
import json
import mimetypes
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()

BASE_DIR = Path(__file__).parent.parent
SITE_DIR = BASE_DIR / "_site"
REPORT_DIR = BASE_DIR / "_audit"
LIGHTHOUSE_VERSION = "13.5.0"
CATEGORIES = ["performance", "accessibility", "best-practices", "seo"]
METRICS = [
    ("first-contentful-paint", "FCP"),
    ("largest-contentful-paint", "LCP"),
    ("total-blocking-time", "TBT"),
    ("cumulative-layout-shift", "CLS"),
]
COMPRESSIBLE = (
    "text/",
    "application/javascript",
    "application/json",
    "application/xml",
    "image/svg+xml",
)


class CompressingHandler(SimpleHTTPRequestHandler):
    """Serve static files with gzip, like the production CDN does."""

    def __init__(self, *args, directory: str, **kwargs) -> None:
        super().__init__(*args, directory=directory, **kwargs)

    def log_message(self, format: str, *args) -> None:
        pass

    def do_GET(self) -> None:
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            path = os.path.join(path, "index.html")
        if not os.path.isfile(path):
            fallback = SITE_DIR / "404.html"
            if self.path != "/404.html" and fallback.is_file():
                path = str(fallback)
            else:
                self.send_error(404)
                return
        data = Path(path).read_bytes()
        content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
        body = data
        extra = {}
        accepts_gzip = "gzip" in self.headers.get("Accept-Encoding", "")
        if (
            accepts_gzip
            and len(data) > 1024
            and content_type.startswith(COMPRESSIBLE)
        ):
            body = gzip.compress(data, compresslevel=9)
            extra["Content-Encoding"] = "gzip"
            extra["Vary"] = "Accept-Encoding"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "public, max-age=3600")
        for key, value in extra.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)


def start_server(directory: Path, port: int) -> ThreadingHTTPServer:
    """Start the compressing static server in a background thread."""
    handler = lambda *args, **kwargs: CompressingHandler(  # noqa: E731
        *args, directory=str(directory), **kwargs
    )
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def lighthouse_runner() -> list[str]:
    """Return the command prefix that runs Lighthouse."""
    if shutil.which("bunx"):
        return ["bunx", f"lighthouse@{LIGHTHOUSE_VERSION}"]
    if shutil.which("npx"):
        return ["npx", "--yes", f"lighthouse@{LIGHTHOUSE_VERSION}"]
    console.print(
        "[red]Neither bunx nor npx was found; install one of them to run "
        "Lighthouse.[/red]"
    )
    sys.exit(1)


def chrome_path() -> str | None:
    """Return a Chrome/Chromium executable path, if one can be found."""
    if os.environ.get("CHROME_PATH"):
        return os.environ["CHROME_PATH"]
    for name in ("chromium", "chromium-browser", "google-chrome", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    return None


def run_lighthouse(
    url: str, device: str, output_path: Path, runner: list[str]
) -> dict | None:
    """Run Lighthouse once and return the parsed report."""
    command = [
        *runner,
        url,
        "--output=json",
        f"--output-path={output_path}",
        "--chrome-flags=--headless=new --no-sandbox --disable-gpu",
        "--only-categories=" + ",".join(CATEGORIES),
        "--quiet",
    ]
    if device == "desktop":
        command.append("--preset=desktop")
    env = dict(os.environ)
    chrome = chrome_path()
    if chrome:
        env["CHROME_PATH"] = chrome
    result = subprocess.run(command, env=env, capture_output=True, text=True)
    if not output_path.is_file():
        console.print(f"  [red]Lighthouse failed:[/red] {result.stderr[:400]}")
        return None
    return json.loads(output_path.read_text())


def summarise(reports: list[dict]) -> dict:
    """Reduce several Lighthouse reports to means and ranges."""
    summary = {"runs": len(reports), "categories": {}, "metrics": {}}
    for category in CATEGORIES:
        values = [
            report["categories"][category]["score"] * 100
            for report in reports
            if report["categories"][category]["score"] is not None
        ]
        if values:
            summary["categories"][category] = (
                statistics.mean(values),
                min(values),
                max(values),
            )
    for audit_id, label in METRICS:
        values = [
            report["audits"][audit_id]["numericValue"]
            for report in reports
            if report["audits"].get(audit_id, {}).get("numericValue") is not None
        ]
        if values:
            summary["metrics"][label] = statistics.mean(values)
    return summary


def measure(
    label: str,
    base_url: str,
    pages: list[str],
    devices: list[str],
    runs: int,
    runner: list[str],
    report_root: Path,
) -> dict:
    """Measure every page on every device and return the collected results."""
    results = {}
    for page in pages:
        for device in devices:
            url = base_url.rstrip("/") + page
            console.print(f"[cyan]→[/cyan] {label} {device} {page} ({runs} run)")
            reports = []
            for run in range(1, runs + 1):
                slug = f"{label}-{device}-{page.strip('/').replace('/', '-') or 'home'}-{run}"
                report_path = report_root / f"{slug}.json"
                report = run_lighthouse(url, device, report_path, runner)
                if report:
                    reports.append(report)
            if reports:
                results[(page, device)] = summarise(reports)
    return results


def show_results(
    local: dict, baseline: dict, pages: list[str], devices: list[str]
) -> None:
    """Print a table of scores, with deltas when a baseline was measured."""
    for page in pages:
        for device in devices:
            key = (page, device)
            if key not in local:
                continue
            local_summary = local[key]
            baseline_summary = baseline.get(key)
            table = Table(
                title=f"{page} — {device} "
                f"({local_summary['runs']} run(s))",
                title_justify="left",
            )
            table.add_column("Metric", style="bold")
            if baseline_summary:
                table.add_column("Deployed", justify="right")
            table.add_column("Local build", justify="right")
            if baseline_summary:
                table.add_column("Change", justify="right")

            for category in CATEGORIES:
                if category not in local_summary["categories"]:
                    continue
                mean, low, high = local_summary["categories"][category]
                row = [category]
                if baseline_summary:
                    base = baseline_summary["categories"].get(category)
                    row.append(f"{base[0]:.0f}" if base else "–")
                row.append(f"{mean:.0f}  [{low:.0f}-{high:.0f}]")
                if baseline_summary:
                    base = baseline_summary["categories"].get(category)
                    row.append(f"{mean - base[0]:+.0f}" if base else "–")
                table.add_row(*row)

            for audit_id, label in METRICS:
                if label not in local_summary["metrics"]:
                    continue
                value = local_summary["metrics"][label]
                shown = f"{value:.3f}" if label == "CLS" else f"{value:.0f} ms"
                row = [label]
                if baseline_summary:
                    base = baseline_summary["metrics"].get(label)
                    if base is not None:
                        base_shown = (
                            f"{base:.3f}" if label == "CLS" else f"{base:.0f} ms"
                        )
                    else:
                        base_shown = "–"
                    row.append(base_shown)
                row.append(shown)
                if baseline_summary:
                    base = baseline_summary["metrics"].get(label)
                    row.append(f"{value - base:+.3f}" if base is not None else "–")
                table.add_row(*row)

            console.print()
            console.print(table)


def main() -> None:
    """Build, serve, measure, and report."""
    parser = argparse.ArgumentParser(
        description="Measure the local production build with Lighthouse",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="reuse the existing _site directory instead of rebuilding",
    )
    parser.add_argument(
        "--baseline",
        metavar="URL",
        help="also measure this deployed URL and show the difference",
    )
    parser.add_argument(
        "--pages",
        nargs="+",
        default=["/"],
        help="page paths to measure (default: /)",
    )
    parser.add_argument(
        "--device",
        choices=["mobile", "desktop", "both"],
        default="both",
        help="device preset (default: both)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=2,
        help="Lighthouse runs per page and device (default: 2)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8901,
        help="port for the local static server (default: 8901)",
    )
    args = parser.parse_args()

    if not args.skip_build:
        console.rule("[bold]Building the site like the publish workflow[/bold]")
        build = subprocess.run(
            ["uv", "run", "python", "scripts/build-local.py"],
            cwd=BASE_DIR,
        )
        if build.returncode != 0:
            console.print("[red]The build failed; stopping.[/red]")
            sys.exit(1)

    if not (SITE_DIR / "index.html").is_file():
        console.print(
            "[red]_site/index.html is missing. Run without --skip-build first.[/red]"
        )
        sys.exit(1)

    report_root = REPORT_DIR
    report_root.mkdir(exist_ok=True)
    devices = ["mobile", "desktop"] if args.device == "both" else [args.device]
    runner = lighthouse_runner()

    server = start_server(SITE_DIR, args.port)
    console.rule(f"[bold]Measuring http://localhost:{args.port}[/bold]")
    try:
        local = measure(
            "local",
            f"http://localhost:{args.port}",
            args.pages,
            devices,
            args.runs,
            runner,
            report_root,
        )
    finally:
        server.shutdown()

    baseline = {}
    if args.baseline:
        console.rule(f"[bold]Measuring {args.baseline}[/bold]")
        baseline = measure(
            "deployed",
            args.baseline,
            args.pages,
            devices,
            args.runs,
            runner,
            report_root,
        )

    show_results(local, baseline, args.pages, devices)
    console.print(
        f"\n[dim]Reports saved in {REPORT_DIR}. Lighthouse reports a "
        "cold-cache, throttled, first visit, so read the range across runs "
        "rather than a single number.[/dim]"
    )


if __name__ == "__main__":
    main()
