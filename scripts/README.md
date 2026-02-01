# Font Awesome Optimization

This directory contains a script to generate a minimal Font Awesome CSS subset
with only the icons you actually use.

## Why?

The full Font Awesome CSS file is **135KB**. Your site only uses **14 icons**,
so we can reduce it to **~2KB** (98.5% reduction!).

## How it works

The script `generate-fontawesome-subset.py`:

1. Scans all `.qmd` and `.yml` files for Font Awesome icon usage
1. Finds icons in `{{< fa ... >}}` and `{{< iconify fa6-solid ... >}}` shortcodes
1. Finds icons in YAML config (navbar/footer)
1. Finds icons in HTML class attributes
1. Automatically detects brand vs solid icons
1. Generates a minimal CSS file (`all.subset.css`) with only those icons
1. Optionally replaces the original `all.css` with the subset (CI only)

## Usage

### Local testing (safe mode)

**Run without modifying the original file:**

```bash
uv run scripts/generate-fontawesome-subset.py
```

This will:

- Create `all.subset.css` with the optimized CSS
- Show size comparison between original and subset
- NOT modify `all.css` (safe for testing)

### CI/production mode

**Run with `--replace` flag to actually replace the original:**

```bash
uv run scripts/generate-fontawesome-subset.py --replace
```

This will:

- Create `all.subset.css` with the optimized CSS
- Create backup at `all.css.backup` (if it doesn't exist)
- Replace `all.css` with the subset
- Used automatically in GitHub Actions

## Adding new icons

The script automatically detects icon usage! Just:

1. Add the icon to your content (e.g., `{{< fa heart >}}` or `{{< fa brands twitter >}}`)
1. Add the icon's unicode to the `ICON_CODES` dict in the script
1. Run the script to test: `uv run scripts/generate-fontawesome-subset.py`
1. The new icon will be included automatically

**For brand icons:** Use `{{< fa brands icon-name >}}` and the script will automatically detect it as a brand icon.

## Finding icon unicode codes

Go to https://fontawesome.com/search and search for your icon. The unicode is
shown on the icon's detail page (e.g., `\f004` for "heart").

## Restoring the full CSS

If you ever need to restore the full Font Awesome CSS:

```bash
cp _extensions/quarto-ext/fontawesome/assets/css/all.css.backup \
   _extensions/quarto-ext/fontawesome/assets/css/all.css
```

## Current icons used

The script currently includes these 14 icons:

- **Solid icons (9):** book-open, circle-left, circle-up, copyright, file-pdf,
  highlighter, megaphone, rocket, rss
- **Brand icons (5):** github, google, linkedin, mastodon, speaker-deck

The script automatically scans:

- All `.qmd` files for `{{< fa ... >}}` and `{{< iconify fa6-solid ... >}}`
  shortcodes
- All `.yml` files for `icon:` declarations
- All `.qmd` and `.html` files for direct `<i class="fa-...">` usage
- Brand icons are detected from `{{< fa brands ... >}}`, `fa-brands` class, and
  common platform names

So you don't need to manually track which icons you're using - just run the script!

## GitHub Actions Integration

The script runs automatically in CI with the `--replace` flag to optimize the
CSS before deployment. Locally, you can safely test without modifying the
original file.
