"""Build the site locally with all optimizations (mimics GitHub Actions workflow)."""

import argparse
import subprocess
import sys
from pathlib import Path

from rich.console import Console

console = Console()

# base directory
BASE_DIR = Path(__file__).parent.parent

INDENT = "  "


def run_command(command: list[str], description: str) -> bool:
    """Run a command and return success status.

    args:
        command: list of command parts to run
        description: human-readable description of what the command does

    returns:
        True if command succeeded, False otherwise
    """
    console.print(f"\n[bold cyan]→[/bold cyan] {description}...")
    try:
        result = subprocess.run(
            command,
            cwd=BASE_DIR,
            check=True,
            capture_output=False,
        )
        console.print(f"{INDENT}[green]✓[/green] {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        console.print(
            f"{INDENT}[red]✗[/red] {description} failed with exit code {e.returncode}"
        )
        return False


def render_site() -> bool:
    """Render the Quarto site (mimics publish.yml render steps)."""
    console.print(
        "\n[bold yellow]════════════════════════════════════════[/bold yellow]"
    )
    console.print("[bold yellow]STEP 1: Render Site[/bold yellow]")
    console.print("[bold yellow]════════════════════════════════════════[/bold yellow]")

    # Run all the publish-site.py stages in order
    steps = [
        (
            ["uv", "run", "python", "scripts/publish-site.py", "--stage", "all"],
            "Pre-render stage (parse bibliography, minify, copy files)",
        ),
        (
            [
                "uv",
                "run",
                "python",
                "scripts/publish-site.py",
                "--stage",
                "render",
                "--render-file",
                "index.qmd",
            ],
            "Render stage (quarto render)",
        ),
        (
            [
                "uv",
                "run",
                "python",
                "scripts/publish-site.py",
                "--stage",
                "post-render",
            ],
            "Post-render stage",
        ),
    ]

    for command, description in steps:
        if not run_command(command, description):
            return False

    return True


def optimize_fontawesome() -> bool:
    """Optimize Font Awesome CSS."""
    console.print(
        "\n[bold yellow]════════════════════════════════════════[/bold yellow]"
    )
    console.print("[bold yellow]STEP 2: Optimize Font Awesome CSS[/bold yellow]")
    console.print("[bold yellow]════════════════════════════════════════[/bold yellow]")

    return run_command(
        ["uv", "run", "python", "scripts/generate-fontawesome-subset.py", "--replace"],
        "Generate Font Awesome subset CSS",
    )


def optimize_bootstrap_icons() -> bool:
    """Optimize Bootstrap Icons CSS."""
    console.print(
        "\n[bold yellow]════════════════════════════════════════[/bold yellow]"
    )
    console.print("[bold yellow]STEP 3: Optimize Bootstrap Icons CSS[/bold yellow]")
    console.print("[bold yellow]════════════════════════════════════════[/bold yellow]")

    return run_command(
        [
            "uv",
            "run",
            "python",
            "scripts/generate-bootstrap-icons-subset.py",
            "--replace",
        ],
        "Generate Bootstrap Icons subset CSS",
    )


def optimize_bootstrap() -> bool:
    """Optimize Bootstrap CSS."""
    console.print(
        "\n[bold yellow]════════════════════════════════════════[/bold yellow]"
    )
    console.print("[bold yellow]STEP 4: Optimize Bootstrap CSS[/bold yellow]")
    console.print("[bold yellow]════════════════════════════════════════[/bold yellow]")

    return run_command(
        ["uv", "run", "python", "scripts/purge-bootstrap-css-simple.py", "--replace"],
        "Purge unused Bootstrap CSS",
    )


def defer_javascript() -> bool:
    """Add defer attributes to JavaScript to prevent render-blocking."""
    console.print(
        "\n[bold yellow]════════════════════════════════════════[/bold yellow]"
    )
    console.print("[bold yellow]STEP 5: Defer JavaScript Loading[/bold yellow]")
    console.print("[bold yellow]════════════════════════════════════════[/bold yellow]")

    return run_command(
        ["uv", "run", "python", "scripts/defer-javascript.py", "--replace"],
        "Add defer attributes to script tags",
    )


def preload_critical_resources() -> bool:
    """Add preload tags for critical resources."""
    console.print(
        "\n[bold yellow]════════════════════════════════════════[/bold yellow]"
    )
    console.print("[bold yellow]STEP 6: Preload Critical Resources[/bold yellow]")
    console.print("[bold yellow]════════════════════════════════════════[/bold yellow]")

    return run_command(
        ["uv", "run", "python", "scripts/preload-critical-resources.py", "--replace"],
        "Add preload tags for critical resources",
    )


def self_host_cdn_resources() -> bool:
    """Self-host CDN resources (jQuery and require.js)."""
    console.print(
        "\n[bold yellow]════════════════════════════════════════[/bold yellow]"
    )
    console.print("[bold yellow]STEP 7: Self-Host CDN Resources[/bold yellow]")
    console.print("[bold yellow]════════════════════════════════════════[/bold yellow]")

    return run_command(
        ["uv", "run", "python", "scripts/self-host-cdn-resources.py", "--replace"],
        "Download and replace CDN resources with local copies",
    )


def main():
    """Build the site locally with all optimizations."""
    parser = argparse.ArgumentParser(
        description="Build site locally (mimics GitHub Actions workflow)"
    )
    parser.add_argument(
        "--skip-render",
        action="store_true",
        help="Skip the render step (only run optimizations)",
    )
    args = parser.parse_args()

    console.print("[bold green]🚀 Local Build Script[/bold green]")
    console.print("This script mimics the GitHub Actions workflow (publish.yml)")
    console.print("It will render the site and run all CSS optimizations.\n")

    # track success of all steps
    all_success = True

    # step 1: render (unless skipped)
    if not args.skip_render:
        if not render_site():
            all_success = False
            console.print("\n[bold red]✗ Render failed! Stopping build.[/bold red]")
            sys.exit(1)
    else:
        console.print("\n[yellow]⊘ Skipping render step (--skip-render)[/yellow]")

    # step 2: optimize Font Awesome
    if not optimize_fontawesome():
        all_success = False

    # step 3: optimize Bootstrap Icons
    if not optimize_bootstrap_icons():
        all_success = False

    # step 4: optimize Bootstrap CSS
    if not optimize_bootstrap():
        all_success = False

    # step 5: defer JavaScript
    if not defer_javascript():
        all_success = False

    # step 6: preload critical resources
    if not preload_critical_resources():
        all_success = False

    # step 7: self-host CDN resources
    if not self_host_cdn_resources():
        all_success = False

    # final summary
    console.print(
        "\n[bold yellow]════════════════════════════════════════[/bold yellow]"
    )
    console.print("[bold yellow]Build Summary[/bold yellow]")
    console.print("[bold yellow]════════════════════════════════════════[/bold yellow]")

    if all_success:
        console.print("\n[bold green]✓ All steps completed successfully![/bold green]")
        console.print("\nNext steps:")
        console.print(
            f"{INDENT}1. Start a local server: cd _site && python3 -m http.server 8000"
        )
        console.print(f"{INDENT}2. Open http://localhost:8000 in your browser")
        console.print(
            f"{INDENT}3. Check DevTools Network tab for font files (should be 200 OK)"
        )
        console.print(f"{INDENT}4. Verify rocket icon renders correctly")
        sys.exit(0)
    else:
        console.print("\n[bold red]✗ Some steps failed! Check output above.[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
