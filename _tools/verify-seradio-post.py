"""Verify a Software Engineering Radio blog post against its transcript.

This tool checks a post written for blog/<slug>/index.qmd against the
automatically generated transcript that Software Engineering Radio
publishes on the episode page. It enforces the rules in AGENTS.md:

  * each quoted passage in the post appears verbatim in the transcript
  * line width is at most 80 characters, with URL-bearing lines reported
    separately because a link cannot be wrapped without breaking it
  * the front matter has the required keys and categories
  * the Introduction, Insights, and Listen sections all exist
  * Insights contains between three and five question headings
  * the podcast shortcode and the back-blog include are present
  * no emoji characters are used, since the site uses Nerd Font icons

For each verified quotation the report shows the speaker and the timestamp
of the transcript turn that contains it. That table is the supporting
evidence that AGENTS.md asks the writing agent to produce.

The report is rendered with rich, which is already declared in
pyproject.toml. rich is used rather than the built-in print
because the repository's ruff configuration selects T201
(flake8-print). A single module-level Console is created below and
every message that the tool emits, including diagnostics, goes through
it. Run the tool through uv run so that the project interpreter and
its dependencies are used::

    uv run _tools/verify-seradio-post.py --post <post> --episode <number>

Calling the script with a bare python3 works only when rich is
installed in that interpreter, since the tool has no other dependencies.
See README.md for how and when to use this tool.

Examples
--------
Verify a post against a transcript that is already on disk::

    uv run _tools/verify-seradio-post.py \
        --post blog/se-radio-scott-kingsley-swagger-ecosystem/index.qmd \
        --transcript ~/.cache/seradio-transcripts/726-transcript.txt

Fetch the transcript from the episode page, then verify it::

    uv run _tools/verify-seradio-post.py \
        --post blog/se-radio-scott-kingsley-swagger-ecosystem/index.qmd \
        --episode 726 --fetch --url <episode-page-url>

Verify the post and check that every link in it resolves::

    uv run _tools/verify-seradio-post.py \
        --post blog/se-radio-jeroen-janssens-thijs-nieuwdorp-polars/index.qmd \
        --episode 727 --check-links

Transcripts are cached outside the repository in
~/.cache/seradio-transcripts so that the published text of an episode
is never committed to this repository.
"""

from __future__ import annotations

import argparse
import html
import importlib
import pathlib
import re
import ssl
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Iterable, Sequence

from rich.console import Console
from rich.table import Table
from rich.text import Text

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE_DIR = pathlib.Path.home() / ".cache" / "seradio-transcripts"
MAX_LINE = 80
URL_TIMEOUT = 30
MIN_QUESTIONS = 3
MAX_QUESTIONS = 5

# match the console style used by the other scripts in this repository
DEFAULT_CONSOLE_STYLE = "bold blue"
PASS_STYLE = "bold green"
FAIL_STYLE = "bold red"
NOTE_STYLE = "yellow"

PASS_ICON = "\uf00c"
FAIL_ICON = "\uf00d"

console = Console()

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# Typographic variants that are accepted as normalizations of the
# transcript text. The episode pages mangle curly double quotes into
# accented i characters, so both spellings must fold together.
NORMALIZE = {
    "\u2019": "'",
    "\u2018": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u00ec": '"',
    "\u00ed": '"',
    "\u00ee": '"',
    "\u2014": "---",
    "\u2013": "--",
}

# Speaker turns look like "Gregory Kapfhammer 00:00:18 Welcome to ...".
TURN_RE = re.compile(
    r"^(?P<speaker>\D{2,40}?)\s+"
    r"(?P<time>\d{1,2}[:'\u2032\u2019]\d{2}[:'\u2032\u2019]\d{2})\s+"
    r"(?P<text>.*)$"
)

FRONT_MATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
QUESTION_RE = re.compile(r"^\*\*(.+?)\*\*$", re.M)
EMOJI_RE = re.compile(
    "[\U0001f000-\U0001faff\U00002600-\U000027bf\U00002b00-\U00002bff\ufe0f]"
)
URL_RE = re.compile(r"https?://[^\s\)\]\"'>]+")

# the markers that end the transcript content on an episode page
END_MARKERS = ("</article>", "<footer", "megaphone-footer", 'id="comments"')

# text that follows the transcript when a page is not trimmed correctly
FOOTER_TEXT = ("What People Are Saying", "Recent posts", "Advertise")


@dataclass
class Turn:
    """A single speaker turn in a transcript."""

    speaker: str
    timestamp: str
    text: str
    normal: str


@dataclass
class Evidence:
    """A verified quotation and the transcript turn that contains it."""

    line: int
    speaker: str
    timestamp: str
    quote: str


def normalize(text: str) -> str:
    """Fold typographic variants and collapse whitespace."""
    for old, new in NORMALIZE.items():
        text = text.replace(old, new)
    return re.sub(r"\s+", " ", text).strip()


def parse_turns(transcript: str) -> list[Turn]:
    """Split transcript text into normalized speaker turns."""
    turns: list[Turn] = []
    for raw in transcript.splitlines():
        line = raw.strip()
        if not line:
            continue
        match = TURN_RE.match(line)
        if match:
            text = match["text"].strip()
            turns.append(
                Turn(
                    match["speaker"].strip(),
                    match["time"],
                    text,
                    normalize(text),
                )
            )
        elif turns:
            # A continuation line belongs to the turn that precedes it.
            turns[-1].text = f"{turns[-1].text} {line}".strip()
            turns[-1].normal = normalize(turns[-1].text)
        else:
            turns.append(Turn("", "", line, normalize(line)))
    return turns


def parse_front_matter(text: str) -> tuple[str, str]:
    """Return the YAML front matter and the body of a post."""
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return "", text
    return match.group(1), text[match.end() :]


def blockquotes(body: str) -> list[tuple[int, str]]:
    """Return (line number, text) for each contiguous blockquote."""
    found: list[tuple[int, str]] = []
    current: list[str] = []
    start = 0
    for number, line in enumerate(body.splitlines(), start=1):
        if line.startswith(">"):
            if not current:
                start = number
            current.append(line.lstrip(">").strip())
        elif current:
            found.append((start, " ".join(current)))
            current = []
    if current:
        found.append((start, " ".join(current)))
    return found


def locate(fragment: str, turns: Sequence[Turn]) -> Turn | None:
    """Find the turn that contains a fragment of a quotation."""
    probe = normalize(fragment).strip().strip('"')
    if not probe:
        return None
    for turn in turns:
        if probe in turn.normal:
            return turn
    joined = " ".join(turn.normal for turn in turns)
    if probe in joined:
        position = joined.index(probe)
        consumed = 0
        for turn in turns:
            consumed += len(turn.normal) + 1
            if consumed > position:
                return turn
    return None


def verify_quotes(body: str, turns: Sequence[Turn]) -> tuple[list[Evidence], list[str]]:
    """Check every quotation against the transcript."""
    evidence: list[Evidence] = []
    problems: list[str] = []
    for line, quote in blockquotes(body):
        fragments = [f for f in normalize(quote).split("...") if f.strip()]
        for fragment in fragments:
            turn = locate(fragment, turns)
            if turn is None:
                problems.append(
                    f"line {line}: quote not found in transcript -> "
                    f"{fragment.strip()[:90]}"
                )
                continue
            evidence.append(
                Evidence(line, turn.speaker, turn.timestamp, fragment.strip())
            )
    return evidence, problems


def check_width(text: str, max_line: int) -> tuple[list[str], list[str]]:
    """Report long lines, separating prose from unbreakable URLs."""
    prose: list[str] = []
    urls: list[str] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if len(line) <= max_line:
            continue
        entry = f"line {number} ({len(line)} chars): {line.strip()[:60]}"
        if "http" in line or "file=" in line:
            urls.append(entry)
        else:
            prose.append(entry)
    return prose, urls


def check_structure(front: str, body: str) -> list[str]:
    """Check front matter, sections, and the required shortcodes."""
    problems: list[str] = []
    if not front:
        return ["missing YAML front matter"]
    for key in (
        "author",
        "title",
        "date",
        "date-format",
        "categories",
        "description",
    ):
        if not re.search(rf"^{key}:", front, re.M):
            problems.append(f"front matter missing: {key}")
    categories = re.search(r"^categories:\s*\[(.*?)\]", front, re.M)
    listed = categories.group(1) if categories else ""
    for required in ("post", "software engineering radio"):
        if required not in listed:
            problems.append(f"categories missing: {required}")
    for section in ("## Introduction", "## Insights", "## Listen"):
        if section not in body:
            problems.append(f"missing section: {section}")
    questions = QUESTION_RE.findall(body)
    if not MIN_QUESTIONS <= len(questions) <= MAX_QUESTIONS:
        problems.append(
            f"expected {MIN_QUESTIONS}-{MAX_QUESTIONS} question "
            f"headings in Insights, found {len(questions)}"
        )
    if "{{< podcast" not in body:
        problems.append("missing podcast shortcode")
    if "{{< include /_back-blog.qmd >}}" not in body:
        problems.append("missing back-blog include")
    emoji = sorted(set(EMOJI_RE.findall(body)))
    if emoji:
        problems.append(f"emoji characters found: {' '.join(emoji)}")
    return problems


def tls_context() -> ssl.SSLContext:
    """Build a TLS context that also works under the uv interpreter.

    The interpreter in .venv does not always locate a system CA bundle
    (for example on NixOS, where /etc/ssl/cert.pem is absent), which
    makes every HTTPS request fail with CERTIFICATE_VERIFY_FAILED. The
    certifi bundle, which the environment already provides, is used
    when the package can be imported, falling back to the default context
    when it cannot.
    """
    try:
        certifi = importlib.import_module("certifi")
    except ModuleNotFoundError:
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=certifi.where())


def check_links(
    text: str, timeout: int = URL_TIMEOUT
) -> tuple[list[tuple[str, str]], list[str]]:
    """Fetch every external link, returning rows and any problems."""
    problems: list[str] = []
    rows: list[tuple[str, str]] = []
    seen: set[str] = set()
    urls = [u.rstrip(".,;:") for u in URL_RE.findall(text)]
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(
                request, timeout=timeout, context=tls_context()
            ) as reply:
                rows.append((str(reply.status), url))
        except urllib.error.HTTPError as error:
            rows.append((str(error.code), url))
            problems.append(f"{url} -> HTTP {error.code}")
        except (urllib.error.URLError, OSError) as error:
            rows.append(("no response", url))
            problems.append(f"{url} -> {error}")
    return rows, problems


def fetch_transcript(url: str, destination: pathlib.Path) -> pathlib.Path:
    """Download an episode page, keeping only the transcript text.

    The page footer that follows the transcript is trimmed, so the cached
    file holds the transcript alone. To fetch a transcript before a post
    exists, use _tools/fetch-seradio-transcript.py, which trims the page
    the same way and also reports the details of the episode.
    """
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urllib.request.urlopen(
        request, timeout=URL_TIMEOUT, context=tls_context()
    ) as reply:
        page = reply.read().decode("utf-8", errors="replace")
    marker = page.lower().find("transcript brought to you")
    if marker < 0:
        raise SystemExit(f"no transcript found at {url}")
    section = page[marker:]
    # the transcript ends where the article, the comments, or the footer
    # of the page starts, so cut the markup at the earliest such marker
    end = len(section)
    for pattern in END_MARKERS:
        hit = section.lower().find(pattern.lower())
        if hit != -1:
            end = min(end, hit)
    section = section[:end]
    section = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", section, flags=re.S)
    section = re.sub(r"<br\s*/?>|</p>|</div>", "\n", section)
    section = re.sub(r"<[^>]+>", "", section)
    section = html.unescape(section)
    section = re.sub(r"[ \t]+", " ", section)
    section = re.sub(r"\n\s*\n+", "\n", section).strip()
    # safety net in case the page markup changes and some site navigation
    # text survives the cut at the end of the transcript content
    for junk in FOOTER_TEXT:
        cut = section.find(junk)
        if cut != -1:
            section = section[:cut].rstrip()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(f"{section}\n", encoding="utf-8")
    return destination


def report(section: str, problems: Iterable[str], count: int = 0) -> bool:
    """Show one check result and return whether it passed."""
    problems = list(problems)
    summary = f"{count} checked" if count else "no issues"
    if problems:
        console.print(
            f"{FAIL_ICON} {section}: ISSUES ({len(problems)})",
            style=FAIL_STYLE,
        )
        for problem in problems:
            console.print(Text(f"     - {problem}", style="red"))
        return False
    console.print(f"{PASS_ICON} {section}: PASS ({summary})", style=PASS_STYLE)
    return True


def show_evidence(evidence: Sequence[Evidence]) -> None:
    """Render the verified quotations as a table."""
    table = Table(
        title=f"{len(evidence)} quotations verified",
        title_style=DEFAULT_CONSOLE_STYLE,
        header_style=DEFAULT_CONSOLE_STYLE,
        show_lines=False,
    )
    table.add_column("#", justify="right", style="dim", no_wrap=True)
    table.add_column("Line", justify="right", no_wrap=True)
    table.add_column("Speaker", no_wrap=True)
    table.add_column("Time", no_wrap=True)
    table.add_column("Quotation")
    for index, item in enumerate(evidence, start=1):
        table.add_row(
            str(index),
            str(item.line),
            Text(item.speaker or "unknown speaker"),
            Text(item.timestamp or "--:--:--"),
            Text(f"{item.quote[:64]}..."),
        )
    console.print(table)


def show_links(rows: Sequence[tuple[str, str]], problems: Sequence[str]) -> bool:
    """Render the result of checking the links in a post."""
    table = Table(
        title=f"{len(rows)} links checked",
        title_style=DEFAULT_CONSOLE_STYLE,
        header_style=DEFAULT_CONSOLE_STYLE,
    )
    table.add_column("Status", justify="right", no_wrap=True)
    table.add_column("URL")
    for status, url in rows:
        style = "green" if status.startswith("2") else "red"
        table.add_row(Text(status, style=style), Text(url))
    console.print(table)
    return report("LINKS", problems, len(rows))


def build_parser() -> argparse.ArgumentParser:
    """Create the command line interface for the tool."""
    parser = argparse.ArgumentParser(
        description=(
            "Verify a Software Engineering Radio blog post against its transcript."
        )
    )
    parser.add_argument(
        "--post",
        required=True,
        type=pathlib.Path,
        help="path to the blog/<slug>/index.qmd file",
    )
    parser.add_argument(
        "--transcript",
        type=pathlib.Path,
        help="path to a transcript text file",
    )
    parser.add_argument(
        "--episode",
        help="episode number, used to find a cached transcript",
    )
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="download the transcript from --url before verifying",
    )
    parser.add_argument(
        "--url",
        help="episode page to download when --fetch is used",
    )
    parser.add_argument(
        "--cache",
        type=pathlib.Path,
        default=CACHE_DIR,
        help=f"transcript cache directory (default: {CACHE_DIR})",
    )
    parser.add_argument(
        "--check-links",
        action="store_true",
        help="fetch every external link in the post",
    )
    parser.add_argument(
        "--strict-width",
        action="store_true",
        help="also fail when a line with an unbreakable URL is too long",
    )
    parser.add_argument(
        "--repo",
        type=pathlib.Path,
        default=REPO_ROOT,
        help=f"repository root (default: {REPO_ROOT})",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the verification and return a process exit code."""
    args = build_parser().parse_args(argv)

    post_path = args.post
    if not post_path.is_absolute():
        post_path = args.repo / post_path
    if not post_path.is_file():
        raise SystemExit(f"post not found: {post_path}")

    if args.fetch:
        if not args.url:
            raise SystemExit("--fetch requires --url")
        name = f"{args.episode or 'transcript'}-transcript.txt"
        args.transcript = fetch_transcript(args.url, args.cache / name)
        console.print(
            f"transcript: fetched to {args.transcript}",
            style=DEFAULT_CONSOLE_STYLE,
        )
    elif not args.transcript and args.episode:
        args.transcript = args.cache / f"{args.episode}-transcript.txt"
    if args.transcript is None:
        raise SystemExit("provide --transcript, or --episode with --fetch")
    if not args.transcript.is_file():
        raise SystemExit(f"transcript not found: {args.transcript}")

    text = post_path.read_text(encoding="utf-8")
    front, body = parse_front_matter(text)
    turns = parse_turns(args.transcript.read_text(encoding="utf-8"))

    console.print(Text(f"post      : {post_path}"), style=DEFAULT_CONSOLE_STYLE)
    console.print(
        Text(f"transcript: {args.transcript} ({len(turns)} turns)"),
        style=DEFAULT_CONSOLE_STYLE,
    )
    console.print(
        Text(f"post size : {len(text)} chars, {len(text.splitlines())} lines"),
        style=DEFAULT_CONSOLE_STYLE,
    )
    console.print()

    evidence, quote_problems = verify_quotes(body, turns)
    prose, urls = check_width(text, MAX_LINE)

    ok = True
    ok &= report("QUOTES", quote_problems, len(evidence))
    ok &= report("STRUCTURE", check_structure(front, body))
    ok &= report("LINE WIDTH", prose)
    if urls:
        label = "also required" if args.strict_width else "unavoidable URLs"
        console.print(
            f"     {len(urls)} line(s) over {MAX_LINE} chars ({label})",
            style=NOTE_STYLE,
        )
        for entry in urls:
            console.print(Text(f"     - {entry}", style=NOTE_STYLE))
        ok &= not args.strict_width
    if args.check_links:
        rows, link_problems = check_links(text)
        ok &= show_links(rows, link_problems)

    console.print()
    show_evidence(evidence)

    console.print()
    if ok:
        console.print(f"{PASS_ICON} RESULT: PASS", style=PASS_STYLE)
        return 0
    console.print(f"{FAIL_ICON} RESULT: FAIL", style=FAIL_STYLE)
    return 1


if __name__ == "__main__":
    sys.exit(main())
