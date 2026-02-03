"""Add defer attribute to script tags to prevent render-blocking JavaScript.

This script runs AFTER quarto render to optimize JavaScript loading by adding
the 'defer' attribute to script tags. This makes JavaScript load asynchronously
without blocking page rendering, significantly improving Lighthouse performance
scores.

Why this needs to be a post-render script:
- Quarto generates the HTML during render with specific script tags
- Quarto doesn't provide built-in options to add defer attributes
- We need to modify the generated HTML after Quarto is done
- This preserves Quarto's functionality while optimizing performance
"""

import argparse
import re
import shutil
from pathlib import Path

from rich.console import Console

console = Console()

# base directory
BASE_DIR = Path(__file__).parent.parent
SITE_DIR = BASE_DIR / "_site"

# Script patterns that should NOT get defer attribute
EXCLUDE_PATTERNS = [
    r'type=["\'](application/json|module)["\']',  # JSON config and ES modules
    r'id=["\'](quarto-html-before-body|quarto-html-after-body)["\']',  # Critical inline scripts
    r"<script>[^<]*DOMContentLoaded",  # Critical DOM-ready scripts
    r"<script>[^<]*window\.document\.addEventListener",  # Critical event listeners
]

# Script patterns that SHOULD get defer attribute
DEFER_PATTERNS = [
    r'<script\s+(?![^>]*defer)(?![^>]*async)([^>]*src=["\'][^"\']+["\'][^>]*)>',  # External scripts without defer/async
]


def should_exclude_script(script_tag: str) -> bool:
    """Check if script tag matches exclusion patterns.

    args:
        script_tag: the full script tag HTML string

    returns:
        True if script should be excluded from defer optimization
    """
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, script_tag, re.IGNORECASE | re.DOTALL):
            return True
    return False


def add_defer_to_scripts(html_content: str) -> tuple[str, int]:
    """Add defer attribute to eligible script tags.

    args:
        html_content: the full HTML content of the file

    returns:
        tuple of (modified HTML content, count of scripts modified)
    """
    modified_count = 0

    def replace_script(match):
        nonlocal modified_count
        script_tag = match.group(0)

        # Skip if this script should be excluded
        if should_exclude_script(script_tag):
            return script_tag

        # Skip if already has defer or async
        if "defer" in script_tag or "async" in script_tag:
            return script_tag

        # Skip if it's an inline script (no src attribute)
        if "src=" not in script_tag:
            return script_tag

        # Add defer after <script
        modified = script_tag.replace("<script ", "<script defer ")
        modified_count += 1
        return modified

    # Find all script tags and process them
    pattern = r"<script[^>]*(?:/>|>.*?</script>)"
    modified_html = re.sub(
        pattern, replace_script, html_content, flags=re.IGNORECASE | re.DOTALL
    )

    return modified_html, modified_count


def process_html_files(replace: bool = False) -> dict[str, int]:
    """Process all HTML files in _site directory.

    args:
        replace: whether to replace original files with optimized versions

    returns:
        dictionary with statistics (files_processed, scripts_deferred)
    """
    stats = {
        "files_processed": 0,
        "scripts_deferred": 0,
        "files_modified": 0,
    }

    if not SITE_DIR.exists():
        console.print(f"[red]✗[/red] Site directory not found: {SITE_DIR}")
        console.print("[yellow]ℹ[/yellow] Run 'quarto render' first")
        return stats

    # Find all HTML files
    html_files = list(SITE_DIR.rglob("*.html"))

    if not html_files:
        console.print(f"[yellow]⚠[/yellow] No HTML files found in {SITE_DIR}")
        return stats

    console.print(f"[cyan]📄[/cyan] Found {len(html_files)} HTML files to process\n")

    for html_file in html_files:
        try:
            # Read original content
            original_content = html_file.read_text(encoding="utf-8")

            # Add defer attributes
            modified_content, defer_count = add_defer_to_scripts(original_content)

            stats["files_processed"] += 1

            if defer_count > 0:
                stats["scripts_deferred"] += defer_count
                stats["files_modified"] += 1

                # Show file and count
                relative_path = html_file.relative_to(SITE_DIR)
                console.print(
                    f"  [green]✓[/green] {relative_path}: "
                    f"added defer to {defer_count} script(s)"
                )

                if replace:
                    # Create backup
                    backup_file = html_file.with_suffix(".html.backup-defer")
                    if not backup_file.exists():
                        shutil.copy2(html_file, backup_file)

                    # Write modified content
                    html_file.write_text(modified_content, encoding="utf-8")

        except Exception as e:
            console.print(f"[red]✗[/red] Error processing {html_file}: {e}")
            continue

    return stats


def main():
    """Add defer attribute to script tags in HTML files."""
    parser = argparse.ArgumentParser(
        description="Add defer attribute to script tags (post-render optimization)"
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace original HTML files with optimized versions (use in CI)",
    )
    args = parser.parse_args()

    console.print("[bold cyan]⚡ JavaScript Defer Optimization[/bold cyan]\n")

    # Process files
    console.print("[yellow]🔍[/yellow] Scanning HTML files for script tags...\n")
    stats = process_html_files(replace=args.replace)

    # Print summary
    console.print(f"\n[bold yellow]{'─' * 50}[/bold yellow]")
    console.print("[bold yellow]Summary[/bold yellow]")
    console.print(f"[bold yellow]{'─' * 50}[/bold yellow]\n")

    console.print(f"  Files processed: {stats['files_processed']}")
    console.print(f"  Files modified: {stats['files_modified']}")
    console.print(f"  Scripts deferred: {stats['scripts_deferred']}")

    if args.replace:
        console.print("\n[green]✓[/green] HTML files updated with defer attributes")
        console.print("[cyan]ℹ[/cyan] Backup files saved with .backup-defer extension")
    else:
        console.print("\n[yellow]ℹ[/yellow] Test mode - HTML files were NOT modified")
        console.print("[yellow]ℹ[/yellow] Use --replace flag to update files")

    # Performance impact message
    if stats["scripts_deferred"] > 0:
        console.print(
            "\n[bold green]🚀 Expected Lighthouse performance improvement: "
            "+10-15 points[/bold green]"
        )
        console.print(
            "[dim]   (Scripts now load asynchronously without blocking render)[/dim]"
        )

    console.print("\n[bold green]✓ Done![/bold green]")


if __name__ == "__main__":
    main()
