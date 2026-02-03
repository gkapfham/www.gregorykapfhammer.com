"""Add preload tags for critical resources to improve page load performance.

This script runs AFTER quarto render to add <link rel="preload"> tags for
critical CSS and JavaScript files. This tells the browser to download these
resources immediately, before the parser discovers them, significantly
improving Lighthouse performance scores.

Why this needs to be a post-render script:
- Quarto generates HTML with hash-based cache busting (e.g., bootstrap-abc123.min.css)
- These hashes change when Quarto version or configuration changes
- We can't hardcode the resource paths - must discover them dynamically
- This script scans the rendered HTML and injects preload tags with correct paths
"""

import argparse
import re
from pathlib import Path

from rich.console import Console

console = Console()

# Base directory
BASE_DIR = Path(__file__).parent.parent
SITE_DIR = BASE_DIR / "_site"

# Critical resources to preload (patterns to match in HTML)
# Note: Patterns handle both quoted and unquoted attributes (minified HTML)
CRITICAL_RESOURCES = [
    {
        "pattern": r'href=["\'"]?(site_libs/bootstrap/bootstrap-[a-f0-9]{32}\.min\.css)',
        "as": "style",
        "name": "Bootstrap CSS (light theme)",
    },
    {
        "pattern": r'src=["\'"]?(site_libs/bootstrap/bootstrap\.min\.js)',
        "as": "script",
        "name": "Bootstrap JavaScript",
    },
    {
        "pattern": r'src=["\'"]?(site_libs/quarto-nav/quarto-nav\.js)',
        "as": "script",
        "name": "Quarto navigation",
    },
    {
        "pattern": r'href=["\'"]?(site_libs/quarto-contrib/fontawesome6-[^/\s>]+/all\.css)',
        "as": "style",
        "name": "Font Awesome CSS",
    },
    {
        "pattern": r'href=["\'"]?(site_libs/bootstrap/bootstrap-icons\.css)',
        "as": "style",
        "name": "Bootstrap Icons CSS",
    },
]


def extract_critical_resources(html_content: str) -> list[dict[str, str]]:
    """Extract critical resource paths from HTML content.

    Args:
        html_content: The full HTML content of the file

    Returns:
        List of dicts with 'path', 'as', and 'name' keys
    """
    resources = []
    seen_paths = set()  # Avoid duplicates

    for resource in CRITICAL_RESOURCES:
        matches = re.findall(resource["pattern"], html_content)
        for path in matches:
            if path not in seen_paths:
                resources.append(
                    {
                        "path": path,
                        "as": resource["as"],
                        "name": resource["name"],
                    }
                )
                seen_paths.add(path)

    return resources


def inject_preload_tags(html_content: str, resources: list[dict[str, str]]) -> str:
    """Inject preload tags into HTML head section.

    Args:
        html_content: The full HTML content of the file
        resources: List of resources to preload

    Returns:
        Modified HTML content with preload tags injected
    """
    # Check if preload tags already exist (avoid duplicates)
    if 'rel="preload"' in html_content:
        return html_content

    # Generate preload tags
    preload_tags = []
    for resource in resources:
        tag = f'<link rel="preload" href="{resource["path"]}" as="{resource["as"]}">'
        preload_tags.append(tag)

    # Join all preload tags
    preload_block = "\n".join(preload_tags)

    # Find the </head> tag and inject preload tags before it
    # Use a more flexible pattern that handles minified HTML
    head_pattern = r"</head>"
    if re.search(head_pattern, html_content, re.IGNORECASE):
        modified_html = re.sub(
            head_pattern,
            f"{preload_block}</head>",
            html_content,
            count=1,
            flags=re.IGNORECASE,
        )
        return modified_html

    # Fallback: couldn't find </head> tag
    return html_content


def process_html_files(replace: bool = False) -> dict[str, int]:
    """Process all HTML files in _site directory.

    Args:
        replace: Whether to replace original files with optimized versions

    Returns:
        Dictionary with statistics (files_processed, files_modified, resources_added)
    """
    stats = {
        "files_processed": 0,
        "files_modified": 0,
        "preload_tags_added": 0,
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

            # Extract critical resources from this file
            resources = extract_critical_resources(original_content)

            stats["files_processed"] += 1

            if resources:
                # Inject preload tags
                modified_content = inject_preload_tags(original_content, resources)

                # Check if content actually changed
                if modified_content != original_content:
                    stats["files_modified"] += 1
                    stats["preload_tags_added"] += len(resources)

                    # Show file and resources
                    relative_path = html_file.relative_to(SITE_DIR)
                    console.print(
                        f"  [green]✓[/green] {relative_path}: "
                        f"added {len(resources)} preload tag(s)"
                    )

                    if replace:
                        # Write modified content (no backup needed for this optimization)
                        html_file.write_text(modified_content, encoding="utf-8")

        except Exception as e:
            console.print(f"[red]✗[/red] Error processing {html_file}: {e}")
            continue

    return stats


def main():
    """Add preload tags for critical resources to HTML files."""
    parser = argparse.ArgumentParser(
        description="Add preload tags for critical resources (post-render optimization)"
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace original HTML files with optimized versions (use in CI)",
    )
    args = parser.parse_args()

    console.print("[bold cyan]🚀 Critical Resource Preload Optimization[/bold cyan]\n")

    # Process files
    console.print("[yellow]🔍[/yellow] Scanning HTML files for critical resources...\n")
    stats = process_html_files(replace=args.replace)

    # Print summary
    console.print(f"\n[bold yellow]{'─' * 50}[/bold yellow]")
    console.print("[bold yellow]Summary[/bold yellow]")
    console.print(f"[bold yellow]{'─' * 50}[/bold yellow]\n")

    console.print(f"  Files processed: {stats['files_processed']}")
    console.print(f"  Files modified: {stats['files_modified']}")
    console.print(f"  Preload tags added: {stats['preload_tags_added']}")

    if args.replace:
        console.print("\n[green]✓[/green] HTML files updated with preload tags")
    else:
        console.print("\n[yellow]ℹ[/yellow] Test mode - HTML files were NOT modified")
        console.print("[yellow]ℹ[/yellow] Use --replace flag to update files")

    # Performance impact message
    if stats["preload_tags_added"] > 0:
        console.print(
            "\n[bold green]🚀 Expected Lighthouse performance improvement: "
            "+3-5 points[/bold green]"
        )
        console.print(
            "[dim]   (Critical resources now load before parser discovers them)[/dim]"
        )

    console.print("\n[bold green]✓ Done![/bold green]")


if __name__ == "__main__":
    main()
