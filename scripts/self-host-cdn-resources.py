"""Self-host jQuery and require.js to eliminate external CDN dependencies.

This script runs AFTER quarto render to improve performance by copying
jQuery and require.js from _include/js to _site/site_libs and updating HTML
references. This eliminates additional TLS handshakes to external domains,
significantly improving mobile Lighthouse scores and reducing Firefox loading
delays.

Why this needs to be a post-render script:
- Quarto's listing feature automatically loads jQuery and require.js from CDN
- This is hardcoded in Quarto's renderer and cannot be configured
- We copy files from _include/js to _site/site_libs
- We replace CDN URLs with local paths in all HTML files
- Eliminates 2 TLS handshakes per page (~150ms each on mobile 4G)

Source files (checked into repository):
- _include/js/jquery.min.js (currently jQuery 3.5.1 from cdnjs)
- _include/js/require.min.js (currently require.js 2.3.6 from cdnjs)

Version handling:
- Script uses regex patterns to match ANY version from cdnjs
- Works with jQuery 3.x, 4.x, etc. and require.js 2.x, 3.x, etc.
- This makes the script resilient to Quarto updating dependency versions
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
SITE_LIBS_DIR = SITE_DIR / "site_libs"
INCLUDE_JS_DIR = BASE_DIR / "_include" / "js"

# CDN resources to self-host
# Uses regex patterns to match ANY version (e.g., 3.5.1, 3.6.0, 4.0.0)
# This makes the script resilient to Quarto updating dependency versions
CDN_RESOURCES = {
    "jquery": {
        # Matches: https://cdnjs.cloudflare.com/ajax/libs/jquery/X.Y.Z/jquery.min.js
        # Where X.Y.Z is any semantic version (e.g., 3.5.1, 3.7.0, 4.0.0)
        "cdn_url_pattern": r"https://cdnjs\.cloudflare\.com/ajax/libs/jquery/[\d.]+/jquery\.min\.js",
        "source_file": INCLUDE_JS_DIR / "jquery.min.js",
        "site_libs_dir": "jquery",
        "site_libs_file": "jquery.min.js",
    },
    "requirejs": {
        # Matches: https://cdnjs.cloudflare.com/ajax/libs/require.js/X.Y.Z/require.min.js
        # Where X.Y.Z is any semantic version (e.g., 2.3.6, 2.4.0, 3.0.0)
        "cdn_url_pattern": r"https://cdnjs\.cloudflare\.com/ajax/libs/require\.js/[\d.]+/require\.min\.js",
        "source_file": INCLUDE_JS_DIR / "require.min.js",
        "site_libs_dir": "requirejs",
        "site_libs_file": "require.min.js",
    },
}


def copy_js_files() -> bool:
    """Copy JS files from _include/js to _site/site_libs.

    returns:
        True if all copies succeeded, False otherwise
    """
    console.print(
        "[yellow]🔍[/yellow] Copying JS files from _include/js to site_libs...\n"
    )

    all_success = True

    for resource_name, resource_info in CDN_RESOURCES.items():
        source_file = resource_info["source_file"]
        site_libs_subdir = SITE_LIBS_DIR / resource_info["site_libs_dir"]
        site_libs_file = site_libs_subdir / resource_info["site_libs_file"]

        # Check if source file exists
        if not source_file.exists():
            console.print(
                f"  [red]✗[/red] {resource_name}: source file not found at {source_file}"
            )
            all_success = False
            continue

        # Create site_libs subdirectory if needed
        site_libs_subdir.mkdir(parents=True, exist_ok=True)

        # Copy file
        try:
            shutil.copy2(source_file, site_libs_file)
            size_kb = site_libs_file.stat().st_size / 1024
            console.print(
                f"  [green]✓[/green] {resource_name}: copied to "
                f"{site_libs_file.relative_to(SITE_DIR)} ({size_kb:.1f}KB)"
            )
        except Exception as e:
            console.print(f"  [red]✗[/red] {resource_name}: copy failed - {e}")
            all_success = False

    return all_success


def calculate_relative_path(html_file: Path, target_dir: str) -> str:
    """Calculate relative path from HTML file to target directory.

    args:
        html_file: path to the HTML file being processed
        target_dir: target directory name (e.g., 'jquery', 'requirejs')

    returns:
        relative path string (e.g., 'site_libs/jquery/' or '../../site_libs/jquery/')
    """
    # Get depth of HTML file relative to _site directory
    relative_to_site = html_file.relative_to(SITE_DIR)
    depth = len(relative_to_site.parts) - 1  # -1 because file itself doesn't count

    if depth == 0:
        # File is at root of _site (e.g., index.html)
        return f"site_libs/{target_dir}/"
    else:
        # File is nested (e.g., blog/post/index.html)
        prefix = "../" * depth
        return f"{prefix}site_libs/{target_dir}/"


def replace_cdn_urls(html_content: str, html_file: Path) -> tuple[str, dict]:
    """Replace CDN URLs with local paths in HTML content.

    args:
        html_content: the full HTML content of the file
        html_file: path to the HTML file being processed

    returns:
        tuple of (modified HTML content, statistics dict)
    """
    stats = {
        "jquery_replaced": 0,
        "requirejs_replaced": 0,
    }

    modified_content = html_content

    # Replace jQuery CDN URL (matches ANY version)
    jquery_info = CDN_RESOURCES["jquery"]
    jquery_cdn_pattern = jquery_info["cdn_url_pattern"]
    jquery_local_path = calculate_relative_path(html_file, jquery_info["site_libs_dir"])
    jquery_local_url = f"{jquery_local_path}{jquery_info['site_libs_file']}"

    # Pattern to match jQuery script tag with ANY version
    # Handles minified HTML: src=URL (no quotes) and src="URL" (with quotes)
    # Matches: <script ... src=https://cdnjs.cloudflare.com/ajax/libs/jquery/X.Y.Z/jquery.min.js ...>
    jquery_script_pattern = (
        rf'<script[^>]*src=["\']?({jquery_cdn_pattern})["\']?[^>]*></script>'
    )

    def replace_jquery(match):
        stats["jquery_replaced"] += 1
        original_tag = match.group(0)
        # Preserve defer if it exists, remove integrity/crossorigin
        if "defer" in original_tag:
            return f"<script defer src={jquery_local_url}></script>"
        else:
            return f"<script src={jquery_local_url}></script>"

    modified_content = re.sub(
        jquery_script_pattern, replace_jquery, modified_content, flags=re.IGNORECASE
    )

    # Replace require.js CDN URL (matches ANY version)
    requirejs_info = CDN_RESOURCES["requirejs"]
    requirejs_cdn_pattern = requirejs_info["cdn_url_pattern"]
    requirejs_local_path = calculate_relative_path(
        html_file, requirejs_info["site_libs_dir"]
    )
    requirejs_local_url = f"{requirejs_local_path}{requirejs_info['site_libs_file']}"

    # Pattern to match require.js script tag with ANY version
    # Handles minified HTML: src=URL (no quotes) and src="URL" (with quotes)
    # Matches: <script ... src=https://cdnjs.cloudflare.com/ajax/libs/require.js/X.Y.Z/require.min.js ...>
    requirejs_script_pattern = (
        rf'<script[^>]*src=["\']?({requirejs_cdn_pattern})["\']?[^>]*></script>'
    )

    def replace_requirejs(match):
        stats["requirejs_replaced"] += 1
        original_tag = match.group(0)
        # Preserve defer if it exists, remove integrity/crossorigin
        if "defer" in original_tag:
            return f"<script defer src={requirejs_local_url}></script>"
        else:
            return f"<script src={requirejs_local_url}></script>"

    modified_content = re.sub(
        requirejs_script_pattern,
        replace_requirejs,
        modified_content,
        flags=re.IGNORECASE,
    )

    return modified_content, stats


def process_html_files(replace: bool = False) -> dict:
    """Process all HTML files in _site directory.

    args:
        replace: whether to replace original files with modified versions

    returns:
        dictionary with statistics
    """
    stats = {
        "files_processed": 0,
        "files_modified": 0,
        "jquery_total_replaced": 0,
        "requirejs_total_replaced": 0,
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

            # Skip if no CDN URLs present
            if (
                "cdnjs.cloudflare.com" not in original_content
                or "jquery" not in original_content.lower()
            ):
                stats["files_processed"] += 1
                continue

            # Replace CDN URLs with local paths
            modified_content, file_stats = replace_cdn_urls(original_content, html_file)

            stats["files_processed"] += 1

            # Check if anything was modified
            total_replacements = (
                file_stats["jquery_replaced"] + file_stats["requirejs_replaced"]
            )

            if total_replacements > 0:
                stats["files_modified"] += 1
                stats["jquery_total_replaced"] += file_stats["jquery_replaced"]
                stats["requirejs_total_replaced"] += file_stats["requirejs_replaced"]

                # Show file and counts
                relative_path = html_file.relative_to(SITE_DIR)
                replacements = []
                if file_stats["jquery_replaced"] > 0:
                    replacements.append(f"jQuery×{file_stats['jquery_replaced']}")
                if file_stats["requirejs_replaced"] > 0:
                    replacements.append(
                        f"require.js×{file_stats['requirejs_replaced']}"
                    )

                console.print(
                    f"  [green]✓[/green] {relative_path}: {', '.join(replacements)}"
                )

                if replace:
                    # Write modified content
                    html_file.write_text(modified_content, encoding="utf-8")

        except Exception as e:
            console.print(f"[red]✗[/red] Error processing {html_file}: {e}")
            continue

    return stats


def main():
    """Self-host CDN resources (jQuery and require.js)."""
    parser = argparse.ArgumentParser(
        description="Self-host CDN resources (post-render optimization)"
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace original HTML files with modified versions (use in CI)",
    )
    args = parser.parse_args()

    console.print("[bold cyan]📦 Self-Host CDN Resources[/bold cyan]\n")

    # Step 1: Copy files from _include/js to site_libs
    if not copy_js_files():
        console.print("\n[red]✗[/red] Failed to copy JS files. Check errors above.")
        return

    # Step 2: Replace CDN URLs in HTML files
    console.print("\n[yellow]🔍[/yellow] Replacing CDN URLs in HTML files...\n")
    stats = process_html_files(replace=args.replace)

    # Print summary
    console.print(f"\n[bold yellow]{'─' * 50}[/bold yellow]")
    console.print("[bold yellow]Summary[/bold yellow]")
    console.print(f"[bold yellow]{'─' * 50}[/bold yellow]\n")

    console.print(f"  Files processed: {stats['files_processed']}")
    console.print(f"  Files modified: {stats['files_modified']}")
    console.print(f"  jQuery URLs replaced: {stats['jquery_total_replaced']}")
    console.print(f"  Require.js URLs replaced: {stats['requirejs_total_replaced']}")

    if args.replace:
        console.print("\n[green]✓[/green] HTML files updated with local resource paths")
        console.print("[green]✓[/green] CDN resources now self-hosted")
    else:
        console.print("\n[yellow]ℹ[/yellow] Test mode - HTML files were NOT modified")
        console.print("[yellow]ℹ[/yellow] Use --replace flag to update files")

    # Performance impact message
    total_replacements = (
        stats["jquery_total_replaced"] + stats["requirejs_total_replaced"]
    )
    if total_replacements > 0:
        console.print(
            "\n[bold green]🚀 Expected Lighthouse performance improvement:[/bold green]"
        )

    console.print("\n[bold green]✓ Done![/bold green]")


if __name__ == "__main__":
    main()
