"""Generate a minimal Font Awesome CSS subset with only the icons actually used."""

import subprocess
from pathlib import Path

from rich.console import Console

console = Console()

# base directory
BASE_DIR = Path(__file__).parent.parent
EXT_CSS = BASE_DIR / "_extensions/quarto-ext/fontawesome/assets/css/all.css"
BACKUP_CSS = BASE_DIR / "_extensions/quarto-ext/fontawesome/assets/css/all.css.backup"

# icon unicode mappings (Font Awesome 6)
ICON_CODES = {
    # solid icons
    "book-open": "\\f518",
    "file-pdf": "\\f1c1",
    "circle-left": "\\f359",
    "circle-up": "\\f35b",
    "copyright": "\\f1f9",
    "rocket": "\\f135",
    "rss": "\\f09e",
    "megaphone": "\\f675",
    "highlighter": "\\f591",
    # brand icons
    "github": "\\f09b",
    "speaker-deck": "\\f83c",
    "mastodon": "\\f4f6",
    "linkedin": "\\f08c",
    "google": "\\f1a0",
}


def find_all_icons():  # noqa: PLR0912
    """Scan all content files and find Font Awesome icons used.

    returns a dict with 'solid' and 'brands' icon sets.
    """
    solid_icons = set()
    brand_icons = set()
    # find {{< fa ... >}} shortcodes
    result = subprocess.run(
        [
            "grep",
            "-roh",
            r"{{< fa [^>]*>}}",
            str(BASE_DIR),
            "--include=*.qmd",
            "--include=*.yml",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    for match in result.stdout.strip().split("\n"):
        if match:
            # extract icon name: {{< fa brands github >}} or {{< fa rocket >}}
            parts = match.replace("{{< fa ", "").replace(" >}}", "").split()
            if len(parts) >= 2 and parts[0] == "brands":
                brand_icons.add(parts[1])  # brand icon
            elif len(parts) >= 1:
                solid_icons.add(parts[-1])  # solid icon
    # find {{< iconify fa6-solid ... >}} shortcodes
    result = subprocess.run(
        [
            "grep",
            "-roh",
            r"{{< iconify fa6-solid [^>]*>}}",
            str(BASE_DIR),
            "--include=*.qmd",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    for match in result.stdout.strip().split("\n"):
        if match:
            # extract icon name: {{< iconify fa6-solid book-open >}}
            parts = (
                match.replace("{{< iconify fa6-solid ", "").replace(" >}}", "").split()
            )
            if parts:
                solid_icons.add(parts[0])
    # find {{< iconify fa6-brands ... >}} shortcodes
    result = subprocess.run(
        [
            "grep",
            "-roh",
            r"{{< iconify fa6-brands [^>]*>}}",
            str(BASE_DIR),
            "--include=*.qmd",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    for match in result.stdout.strip().split("\n"):
        if match:
            # extract icon name: {{< iconify fa6-brands github >}}
            parts = (
                match.replace("{{< iconify fa6-brands ", "").replace(" >}}", "").split()
            )
            if parts:
                brand_icons.add(parts[0])
    # find "icon: name" in YAML files (navbar/footer icons)
    # these are typically brand icons for social media platforms
    common_brand_platforms = {
        "github",
        "gitlab",
        "mastodon",
        "linkedin",
        "twitter",
        "x-twitter",
        "facebook",
        "instagram",
        "youtube",
        "google",
        "speaker-deck",
        "stackoverflow",
        "reddit",
        "discord",
        "slack",
    }
    result = subprocess.run(
        ["grep", "-rh", r"icon:", str(BASE_DIR), "--include=*.yml"],
        capture_output=True,
        text=True,
        check=False,
    )
    for line in result.stdout.strip().split("\n"):
        if line and "icon:" in line:
            # extract icon name: "    icon: github" or "icon: megaphone"
            icon_name = line.split("icon:")[-1].strip()
            if icon_name and not icon_name.startswith('"'):
                # check if it's a common brand platform
                if icon_name in common_brand_platforms:
                    brand_icons.add(icon_name)
                else:
                    solid_icons.add(icon_name)
    # find direct class usage: <i class="fa-solid fa-highlighter">
    result = subprocess.run(
        [
            "grep",
            "-roh",
            r'class="fa-[^"]*"',
            str(BASE_DIR),
            "--include=*.qmd",
            "--include=*.html",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    for match in result.stdout.strip().split("\n"):
        if match:
            # extract icon names from class="fa-solid fa-circle-left"
            classes = match.replace('class="', "").replace('"', "").split()
            is_brand = "fa-brands" in classes
            for cls in classes:
                if cls.startswith("fa-") and cls not in [
                    "fa-solid",
                    "fa-brands",
                    "fa-regular",
                ]:
                    icon_name = cls.replace("fa-", "")
                    if is_brand:
                        brand_icons.add(icon_name)
                    else:
                        solid_icons.add(icon_name)
    return {"solid": sorted(solid_icons), "brands": sorted(brand_icons)}


def generate_css(icons_dict):
    """Generate minimal Font Awesome CSS with only specified icons.

    args:
        icons_dict: dict with 'solid' and 'brands' keys containing icon lists
    """
    solid_icons = icons_dict["solid"]
    brand_icons = icons_dict["brands"]
    css = """/* minimal Font Awesome subset - only icons actually used */
/* auto-generated by scripts/generate-fontawesome-subset.py */

/* base styles */
.fa, .fas, .fa-solid, .fab, .fa-brands {
  -moz-osx-font-smoothing: grayscale;
  -webkit-font-smoothing: antialiased;
  display: var(--fa-display, inline-block);
  font-style: normal;
  font-variant: normal;
  line-height: 1;
  text-rendering: auto;
}

.fa, .fas, .fa-solid {
  font-family: "Font Awesome 6 Free";
  font-weight: 900;
}

.fab, .fa-brands {
  font-family: "Font Awesome 6 Brands";
  font-weight: 400;
}

/* sizing classes */
.fa-sm { font-size: 0.875em; line-height: 0.0714285705em; vertical-align: 0.0535714295em; }
.fa-lg { font-size: 1.25em; line-height: 0.05em; vertical-align: -0.075em; }
.fa-xl { font-size: 1.5em; line-height: 0.0416666682em; vertical-align: -0.125em; }
.fa-2xl { font-size: 2em; line-height: 0.03125em; vertical-align: -0.1875em; }
.fa-2x { font-size: 2em; }
.fa-3x { font-size: 3em; }
.fa-4x { font-size: 4em; }
.fa-5x { font-size: 5em; }

/* icon definitions */
"""
    # add solid icons
    if solid_icons:
        css += "\n/* solid icons */\n"
        for icon in solid_icons:
            if icon in ICON_CODES:
                css += f'.fa-{icon}:before {{ content: "{ICON_CODES[icon]}"; }}\n'
    # add brand icons
    if brand_icons:
        css += "\n/* brand icons */\n"
        for icon in brand_icons:
            if icon in ICON_CODES:
                css += f'.fa-{icon}:before {{ content: "{ICON_CODES[icon]}"; }}\n'
    # add font faces
    css += """
/* font faces */
@font-face {
  font-family: 'Font Awesome 6 Free';
  font-style: normal;
  font-weight: 900;
  font-display: swap;
  src: url("../webfonts/fa-solid-900.woff2") format("woff2");
}

@font-face {
  font-family: 'Font Awesome 6 Brands';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url("../webfonts/fa-brands-400.woff2") format("woff2");
}
"""
    return css


def main():
    """Generate the Font Awesome subset CSS file."""
    console.print(":magnifying_glass_tilted_left: Scanning for Font Awesome icons...")
    icons_dict = find_all_icons()
    total_icons = len(icons_dict["solid"]) + len(icons_dict["brands"])
    if total_icons == 0:
        console.print(":cross_mark: No icons found!")
        return
    console.print(f":check_mark_button: Found {total_icons} unique icons:")
    console.print(f"   Solid icons ({len(icons_dict['solid'])}):")
    for icon in icons_dict["solid"]:
        console.print(f"      - {icon}")
    console.print(f"   Brand icons ({len(icons_dict['brands'])}):")
    for icon in icons_dict["brands"]:
        console.print(f"      - {icon}")
    # create backup if it doesn't exist
    if not BACKUP_CSS.exists() and EXT_CSS.exists():
        console.print(f"\n:package: Creating backup: {BACKUP_CSS.name}")
        EXT_CSS.rename(BACKUP_CSS)
        EXT_CSS.write_text(BACKUP_CSS.read_text())
    # generate and write minimal CSS
    console.print("\n:pencil: Generating minimal CSS...")
    css = generate_css(icons_dict)
    EXT_CSS.write_text(css)
    # show size comparison
    if BACKUP_CSS.exists():
        original_size = BACKUP_CSS.stat().st_size
        new_size = EXT_CSS.stat().st_size
        reduction = ((original_size - new_size) / original_size) * 100
        console.print("\n:bar_chart: Size comparison:")
        console.print(f"   Original: {original_size:,} bytes")
        console.print(f"   Subset:   {new_size:,} bytes")
        console.print(f"   Reduction: {reduction:.1f}%")
    console.print("\n:party_popper: Done! Minimal CSS generated at:")
    console.print(f"   {EXT_CSS.relative_to(BASE_DIR)}")
    console.print(
        "\n:light_bulb: Remember to run 'quarto render' to rebuild your site!"
    )


if __name__ == "__main__":
    main()
