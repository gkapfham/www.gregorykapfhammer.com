"""Remove the inappropriate role=menu from the Quarto navbar toggler button.

Quarto's built-in template emits role="menu" on the navbar toggler
button. The Lighthouse "Accessibility tree is not well-formed" audit
(Agentic Browsing category) flags this because the menu role requires
menuitem children and menu keyboard semantics. The toggler button
controls a Bootstrap collapse, so its native button semantics are the
correct ones and the role attribute must be removed.

This script runs AFTER render, like the other post-render optimization
scripts, and rewrites every HTML file in the output directory.
"""

import argparse
import re
from pathlib import Path

from rich.console import Console

console = Console()

# Matches the toggler button and captures everything before role=menu so
# the role attribute (quoted or unquoted) can be dropped.
TOGGLER_ROLE_PATTERN = re.compile(
    r'(<button[^>]*navbar-toggler[^>]*)\s+role=("menu"|menu)(?=[\s>])'
)


def fix_file(path: Path) -> bool:
    """Remove role=menu from the toggler button in one HTML file."""
    text = path.read_text(encoding="utf-8")
    if "navbar-toggler" not in text:
        return False
    new = TOGGLER_ROLE_PATTERN.sub(r"\1", text)
    if new == text:
        return False
    path.write_text(new, encoding="utf-8")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove role=menu from the navbar toggler button."
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
    for html_file in directory.rglob("*.html"):
        total += 1
        if fix_file(html_file):
            patched += 1

    console.print(
        f"[green]✓[/green] Removed role=menu from toggler buttons "
        f"in {patched} of {total} HTML files"
    )


if __name__ == "__main__":
    main()
