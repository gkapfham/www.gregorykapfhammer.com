# Font Awesome Optimization

This directory contains a script to generate a minimal Font Awesome CSS subset with only the icons you actually use.

## Why?

The full Font Awesome CSS file is **135KB**. Your site only uses **13 icons**, so we can reduce it to **~2KB** (98.5% reduction!).

## How it works

The script `generate-fontawesome-subset.py`:
1. Scans all `.qmd` and `.yml` files for Font Awesome icon usage
2. Finds icons in `{{< fa ... >}}` and `{{< iconify fa6-solid ... >}}` shortcodes
3. Finds icons in YAML config (navbar/footer)
4. Generates a minimal CSS file with only those icons
5. Replaces the full Font Awesome CSS in `_extensions/quarto-ext/fontawesome/assets/css/all.css`

## Usage

**Run this script whenever you add new Font Awesome icons to your site:**

```bash
python scripts/generate-fontawesome-subset.py
```

Then rebuild your site:

```bash
quarto render
```

## Adding new icons

1. Add the icon to your content (e.g., `{{< fa heart >}}`)
2. Add the icon's unicode to the `ICON_CODES` dict in the script
3. Run the script to regenerate the CSS
4. Rebuild your site

## Finding icon unicodes

Go to https://fontawesome.com/search and search for your icon. The unicode is shown on the icon's detail page (e.g., `\f004` for "heart").

## Restoring the full CSS

If you ever need to restore the full Font Awesome CSS:

```bash
cp _extensions/quarto-ext/fontawesome/assets/css/all.css.backup \
   _extensions/quarto-ext/fontawesome/assets/css/all.css
```

## Current icons used

The script currently includes these 14 icons:
- **Solid icons:** book-open, file-pdf, circle-left, circle-up, copyright, rocket, rss, megaphone, highlighter
- **Brand icons:** github, speaker-deck, mastodon, linkedin, google

The script automatically scans:
- All `.qmd` files for `{{< fa ... >}}` and `{{< iconify fa6-solid ... >}}` shortcodes
- All `.yml` files for `icon:` declarations  
- All `.qmd` and `.html` files for direct `<i class="fa-...">` usage

So you don't need to manually track which icons you're using - just run the script!
