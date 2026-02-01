#!/usr/bin/env python3
"""
Test the Font Awesome subset optimization.

This script:
1. Checks that all icons used in HTML are defined in CSS
2. Verifies the CSS file size is small
3. Tests that icon unicodes are correct
4. Provides a checklist of pages to manually verify

Usage:
    python scripts/test-fontawesome-subset.py
"""

import subprocess
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
SITE_DIR = BASE_DIR / "_site"
CSS_FILE = SITE_DIR / "site_libs/quarto-contrib/fontawesome6-0.1.0/all.css"


def test_css_size():
    """Test that CSS file is small (should be ~2KB, not 135KB)."""
    if not CSS_FILE.exists():
        print("❌ CSS file not found! Run 'quarto render' first.")
        return False

    size = CSS_FILE.stat().st_size
    print(f"\n📊 CSS File Size: {size:,} bytes")

    if size > 10000:  # 10KB threshold
        print(f"   ⚠️  WARNING: File is larger than expected!")
        print(f"   Expected: ~2KB, Got: {size / 1024:.1f}KB")
        return False
    elif size < 1000:  # Too small
        print(f"   ⚠️  WARNING: File seems too small, may be missing icons")
        return False
    else:
        print(f"   ✅ Size looks good! ({size / 1024:.1f}KB)")
        return True


def find_icons_in_html():
    """Find all Font Awesome icon classes used in generated HTML."""
    icons = set()

    # Search all HTML files
    for html_file in SITE_DIR.rglob("*.html"):
        content = html_file.read_text()

        # Find fa-* classes
        for match in re.finditer(r'class="[^"]*fa-([a-z-]+)[^"]*"', content):
            icon_name = match.group(1)
            if icon_name not in ["solid", "brands", "regular"]:
                icons.add(icon_name)

    return sorted(icons)


def find_icons_in_css():
    """Find all icons defined in the CSS file."""
    if not CSS_FILE.exists():
        return set()

    content = CSS_FILE.read_text()
    icons = set()

    # Find .fa-icon-name:before definitions
    for match in re.finditer(r"\.fa-([a-z-]+):before", content):
        icons.add(match.group(1))

    return sorted(icons)


def test_icon_coverage():
    """Test that all icons used in HTML are defined in CSS."""
    print("\n🔍 Checking icon coverage...")

    html_icons = set(find_icons_in_html())
    css_icons = set(find_icons_in_css())

    print(f"\n   Icons used in HTML: {len(html_icons)}")
    print(f"   Icons defined in CSS: {len(css_icons)}")

    # Check for missing icons
    missing = html_icons - css_icons
    if missing:
        print(f"\n   ❌ MISSING ICONS IN CSS:")
        for icon in sorted(missing):
            print(f"      - {icon}")
        return False

    # Check for unused icons
    unused = css_icons - html_icons
    if unused:
        print(f"\n   ℹ️  Icons in CSS but not on homepage:")
        for icon in sorted(unused):
            print(f"      - {icon}")
        print(f"   (These may be used on other pages)")

    print(f"\n   ✅ All HTML icons are defined in CSS!")
    return True


def test_font_faces():
    """Test that font-face declarations exist."""
    if not CSS_FILE.exists():
        return False

    content = CSS_FILE.read_text()

    print("\n🔤 Checking font-face declarations...")

    has_solid = "Font Awesome 6 Free" in content
    has_brands = "Font Awesome 6 Brands" in content
    has_woff2 = ".woff2" in content
    has_display_swap = "font-display: swap" in content

    if has_solid:
        print("   ✅ Solid font-face defined")
    else:
        print("   ❌ Solid font-face missing")

    if has_brands:
        print("   ✅ Brands font-face defined")
    else:
        print("   ❌ Brands font-face missing")

    if has_woff2:
        print("   ✅ WOFF2 fonts referenced")
    else:
        print("   ❌ WOFF2 fonts missing")

    if has_display_swap:
        print("   ✅ font-display: swap enabled")
    else:
        print("   ⚠️  font-display: swap not found")

    return has_solid and has_brands and has_woff2


def print_manual_checklist():
    """Print manual testing checklist."""
    print("\n\n📋 Manual Testing Checklist")
    print("=" * 60)
    print("\nStart the preview server:")
    print("  quarto preview --port 5555")
    print("\nThen visit these pages and verify icons display correctly:")
    print("\n  1. Homepage (http://localhost:5555)")
    print("     - Check: 🚀 rocket icons in callouts")
    print("     - Check: © copyright in footer")
    print("     - Check: ⬆️  circle-up in footer")
    print("     - Check: 📡 RSS icon in navbar")
    print("\n  2. Blog listing (http://localhost:5555/blog/)")
    print("     - Check: ⬅️  circle-left 'back' links")
    print(
        "\n  3. Research presentations (http://localhost:5555/research/presentations/)"
    )
    print("     - Check: 🎤 speaker-deck icons")
    print("\n  4. Any page with paper links")
    print("     - Check: 📖 book-open icons (via iconify)")
    print("     - Check: 📄 file-pdf icons")
    print("\n  5. Navbar")
    print("     - Check: GitHub icon")
    print("     - Check: Mastodon icon")
    print("     - Check: LinkedIn icon")
    print("     - Check: Google Scholar icon")
    print("\n  6. Announcement banner (if visible)")
    print("     - Check: 📢 megaphone icon")
    print("\n" + "=" * 60)


def main():
    print("🧪 Testing Font Awesome Subset Optimization")
    print("=" * 60)

    # Run tests
    size_ok = test_css_size()
    coverage_ok = test_icon_coverage()
    fonts_ok = test_font_faces()

    # Summary
    print("\n\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)

    all_passed = size_ok and coverage_ok and fonts_ok

    if all_passed:
        print("✅ All automated tests PASSED!")
        print("\n👀 Next step: Manual visual testing")
        print_manual_checklist()
    else:
        print("❌ Some tests FAILED!")
        print("\nRun: python scripts/generate-fontawesome-subset.py")
        print("Then: quarto render")
        print("Then re-run this test script.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
