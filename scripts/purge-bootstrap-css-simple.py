"""Purge unused Bootstrap CSS using PurgeCSS with minimal configuration."""

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from rich.console import Console

console = Console()

# Base directory
BASE_DIR = Path(__file__).parent.parent
SITE_LIBS = BASE_DIR / "_site/site_libs/bootstrap"


def purge_css_file(css_file_path, dry_run=True):
    """Purge unused CSS from a Bootstrap CSS file using PurgeCSS defaults.

    This uses PurgeCSS's default behavior with NO safelist, letting it
    automatically detect all used classes from HTML and JS files.

    Args:
        css_file_path: Path to the CSS file to purge
        dry_run: If True, only show what would be purged (no changes)

    Returns:
        tuple: (success: bool, original_size: int, purged_size: int)
    """
    css_file = Path(css_file_path)

    if not css_file.exists():
        console.print(f":cross_mark: File not found: {css_file.name}")
        return (False, 0, 0)

    original_size = css_file.stat().st_size

    try:
        console.print(f"\n:scissors: Purging {css_file.name}...")
        console.print(
            "   Using PurgeCSS defaults (no safelist, auto-detect from HTML+JS)..."
        )

        # Create temp directory for output
        temp_dir = tempfile.mkdtemp(prefix="purgecss_")

        # Run PurgeCSS with MINIMAL config:
        # - Scan all HTML files
        # - Scan all JS files (important for dynamic classes!)
        # - No safelist (let PurgeCSS auto-detect everything)
        # - Keep CSS variables, keyframes, fonts
        cmd = [
            "npx",
            "purgecss",
            "--css",
            str(css_file),
            "--content",
            str(BASE_DIR / "_site/**/*.html"),
            str(BASE_DIR / "_site/**/*.js"),
            "--output",
            temp_dir,
            "--variables",  # Keep CSS variables
            "--keyframes",  # Keep animations
            "--font-face",  # Keep font declarations
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )

        # Read the purged CSS from temp directory
        purged_file = Path(temp_dir) / css_file.name
        if not purged_file.exists():
            console.print(":cross_mark: PurgeCSS did not create output file")
            shutil.rmtree(temp_dir)
            return (False, original_size, 0)

        purged_css = purged_file.read_text()
        purged_size = len(purged_css.encode("utf-8"))

        if dry_run:
            console.print(f":information: [DRY RUN] Would reduce {css_file.name}:")
            console.print(
                f"   Original: {original_size:,} bytes ({original_size / 1024:.1f} KB)"
            )
            console.print(
                f"   Purged:   {purged_size:,} bytes ({purged_size / 1024:.1f} KB)"
            )
            reduction = ((original_size - purged_size) / original_size) * 100
            console.print(f"   Reduction: {reduction:.1f}%")
            shutil.rmtree(temp_dir)
            return (True, original_size, purged_size)
        else:
            # Create backup
            backup_file = css_file.with_suffix(".css.backup")
            if not backup_file.exists():
                console.print(f":package: Creating backup: {backup_file.name}")
                shutil.copy2(css_file, backup_file)

            # Write purged CSS
            os.chmod(css_file, 0o600)  # Make writable
            css_file.write_text(purged_css)
            console.print(f":check_mark: Purged {css_file.name}")
            console.print(
                f"   Original: {original_size:,} bytes ({original_size / 1024:.1f} KB)"
            )
            console.print(
                f"   Purged:   {purged_size:,} bytes ({purged_size / 1024:.1f} KB)"
            )
            reduction = ((original_size - purged_size) / original_size) * 100
            console.print(f"   Reduction: {reduction:.1f}%")
            shutil.rmtree(temp_dir)
            return (True, original_size, purged_size)

    except subprocess.CalledProcessError as e:
        console.print(f":cross_mark: PurgeCSS failed: {e}")
        console.print(f"Error output: {e.stderr}")
        if "temp_dir" in locals():
            shutil.rmtree(temp_dir)
        return (False, original_size, 0)


def main():  # noqa: PLR0915
    """Main function to purge Bootstrap CSS files."""
    parser = argparse.ArgumentParser(
        description="Purge unused Bootstrap CSS using PurgeCSS defaults"
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Actually purge the CSS files (default is dry-run mode)",
    )
    args = parser.parse_args()

    console.print(
        ":scissors: Bootstrap CSS Purge Tool (Default Mode)", style="bold cyan"
    )
    console.print()

    # Check if _site exists
    if not SITE_LIBS.exists():
        console.print(":cross_mark: _site/site_libs/bootstrap/ directory not found!")
        console.print(":information: Run 'quarto render' first to generate the site.")
        return

    # Check if npx is available
    console.print(":magnifying_glass_tilted_left: Checking for npx...")
    try:
        subprocess.run(
            ["npx", "--version"],
            capture_output=True,
            check=True,
        )
        console.print(":check_mark: npx is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print(":cross_mark: npx not found!")
        console.print(":information: Please install Node.js and npm to use this tool.")
        return

    # Show mode
    if args.replace:
        console.print(
            "\n:warning: REPLACE MODE - Files will be modified!", style="bold red"
        )
    else:
        console.print(
            "\n:information: DRY RUN MODE - No files will be modified",
            style="bold green",
        )
        console.print(
            ":information: Use --replace flag to actually purge the CSS files"
        )

    # Find CSS files
    console.print(
        f"\n:magnifying_glass_tilted_left: Looking for Bootstrap CSS files in {SITE_LIBS}..."
    )
    css_files = list(SITE_LIBS.glob("bootstrap*.min.css"))

    if not css_files:
        console.print(":cross_mark: No Bootstrap CSS files found!")
        return

    console.print(f":check_mark: Found {len(css_files)} CSS files:")
    for css_file in css_files:
        console.print(f"   - {css_file.name}")

    console.print(
        "\n:light_bulb: Strategy: Let PurgeCSS auto-detect classes from HTML and JS"
    )
    console.print(":light_bulb: No safelist - PurgeCSS will scan all content files")

    # Process each CSS file
    total_original = 0
    total_purged = 0
    success_count = 0

    for css_file in css_files:
        success, original, purged = purge_css_file(css_file, dry_run=not args.replace)
        if success:
            success_count += 1
            total_original += original
            total_purged += purged

    # Summary
    console.print("\n" + "=" * 60)
    console.print(":bar_chart: Summary", style="bold")
    console.print(f"Files processed: {success_count}/{len(css_files)}")
    console.print(
        f"Total original size: {total_original:,} bytes ({total_original / 1024:.1f} KB)"
    )
    console.print(
        f"Total purged size: {total_purged:,} bytes ({total_purged / 1024:.1f} KB)"
    )
    if total_original > 0:
        total_reduction = ((total_original - total_purged) / total_original) * 100
        savings = total_original - total_purged
        console.print(
            f"Total reduction: {total_reduction:.1f}% ({savings:,} bytes saved)"
        )

    if not args.replace:
        console.print(
            "\n:information: This was a dry run. Use --replace to apply changes."
        )
        console.print(
            "\n:light_bulb: After applying changes, test your site thoroughly:"
        )
        console.print("   1. Run: python -m http.server 8000 --directory _site")
        console.print("   2. Open: http://localhost:8000")
        console.print("   3. Test: Navigation, dropdowns, buttons, forms, dark mode")
        console.print("   4. Test: Resize browser to check responsive breakpoints")
    else:
        console.print("\n:party_popper: Purge complete!")
        console.print("\n:warning: IMPORTANT: Test your site before deploying:")
        console.print("   1. Run: python -m http.server 8000 --directory _site")
        console.print("   2. Open: http://localhost:8000")
        console.print("   3. Test all interactive elements thoroughly")

    console.print()


if __name__ == "__main__":
    main()
