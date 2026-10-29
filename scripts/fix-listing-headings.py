"""Retag listing item titles from h3 to h2 so the heading order is valid.

Quarto's default listing template emits every item title as an h3:

    <h3 class="no-anchor listing-title"><a ...>Title</a></h3>

A listing page has a single h1 and no h2, so the outline jumps from level 1
straight to level 3. Lighthouse's heading-order audit reports that skip
("Heading elements are not in a sequentially-descending order"), and screen
readers get a broken outline for the page.

Each listed item is a section of the listing page, so level 2 is the correct
level for the title. This script rewrites the tag after render, which keeps
the change in one place instead of duplicating Quarto's listing template.
The h2 is much larger than the h3 by default, so styles.css pins
`div.quarto-post .body h2.listing-title` back to the h3 type scale and the
rendered size does not change.

Like the other post-render scripts, this one runs after render (and after
the HTML has been minified) and rewrites every HTML file in the output
directory. It is idempotent: a second run finds no h3 listing titles.
"""

import argparse
import re
from pathlib import Path

from rich.console import Console

console = Console()

# Matches an h3 whose class list contains listing-title, with the whole
# opening tag captured so the attributes are preserved. Titles cannot
# contain a closing h3 tag, so the non-greedy body match is safe.
LISTING_TITLE_PATTERN = re.compile(
    r'<h3\b([^>]*\bclass="[^"]*\blisting-title\b[^"]*"[^>]*)>(.*?)</h3>',
    re.DOTALL,
)


def fix_file(path: Path) -> tuple[bool, int]:
    """Retag h3 listing titles as h2 in one HTML file."""
    text = path.read_text(encoding="utf-8")
    if "listing-title" not in text:
        return (False, 0)
    new, count = LISTING_TITLE_PATTERN.subn(r"<h2\1>\2</h2>", text)
    if count == 0:
        return (False, 0)
    path.write_text(new, encoding="utf-8")
    return (True, count)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Retag listing item titles from h3 to h2."
    )
    parser.add_argument(
        "-d",
        "--directory",
        default="_site",
        help="Output directory to process (default: _site)",
    )
    args = parser.parse_args()

    directory = Path(args.directory)
    if not directory.is_dir():
        console.print(f"[red]Directory not found: {directory}[/red]")
        raise SystemExit(1)

    patched = 0
    total = 0
    headings = 0
    for html_file in directory.rglob("*.html"):
        total += 1
        changed, count = fix_file(html_file)
        if changed:
            patched += 1
            headings += count

    console.print(
        f"[green]✓[/green] Retagged {headings} listing titles h3 -> h2 "
        f"in {patched} of {total} HTML files"
    )


if __name__ == "__main__":
    main()
