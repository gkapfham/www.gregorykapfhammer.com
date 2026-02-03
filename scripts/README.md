# Website Build Scripts

This directory contains Python scripts that automate various aspects of building
and publishing the www.gregorykapfhammer.com website. These scripts handle
bibliography parsing, file optimization, asset copying, and deployment.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Script Descriptions](#script-descriptions)
  - [build-local.py](#build-localpy)
  - [parse-bibliography.py](#parse-bibliographypy)
  - [generate-fontawesome-subset.py](#generate-fontawesome-subsetpy)
  - [test-fontawesome-subset.py](#test-fontawesome-subsetpy)
  - [generate-bootstrap-icons-subset.py](#generate-bootstrap-icons-subsetpy)
  - [purge-bootstrap-css-simple.py](#purge-bootstrap-css-simplepy)
  - [defer-javascript.py](#defer-javascriptpy)
  - [minify-files.py](#minify-filespy)
  - [copy-files.py](#copy-filespy)
  - [publish-site.py](#publish-sitepy)
- [Build Pipeline](#build-pipeline)
- [Common Patterns](#common-patterns)

______________________________________________________________________

## Overview

All scripts are designed to work with the Quarto-based website and follow these
conventions:

- **Environment detection**: Most scripts check for `QUARTO_PROJECT_RENDER_ALL`
  environment variable to avoid running during preview mode
- **Force flag**: Use `-f` or `--force` to override environment detection
- **Rich output**: Scripts use `rich.console.Console` for formatted output
- **UV integration**: Scripts run with `uv run` to access project dependencies

______________________________________________________________________

## Quick Start

### Fast Optimization Workflow (Recommended for Testing)

**If you already have `_site/` from a previous build**, run optimizations only:

```bash
# Skip slow quarto render, only run optimizations (FAST!)
uv run python scripts/build-local.py --skip-render

# Then test locally
cd _site
python3 -m http.server 8000
# Open http://localhost:8000 in browser
```

**This is perfect for:**
- Testing CSS/JS optimizations quickly
- Iterating on optimization scripts
- Verifying changes before committing

### Full Build (When Content Changes)

Build the site from scratch with all optimizations:

```bash
# Full build: render + all optimizations (SLOW - 5+ minutes)
uv run python scripts/build-local.py

# Then test locally
cd _site
python3 -m http.server 8000
# Open http://localhost:8000 in browser
```

**Use this when:**
- You've edited `.qmd` content files
- You need a fresh build
- You're testing after pulling from GitHub

### Development Preview

For rapid iteration during content development:

```bash
# Live preview without running optimization scripts
quarto preview
```

### Manual Build Steps

If you need fine-grained control over the build process:

```bash
# Step 1: Pre-render (parse bibliography)
uv run python scripts/publish-site.py --stage all

# Step 2: Render site
uv run python scripts/publish-site.py --stage render --render-file index.qmd

# Step 3: Post-render (minify, copy files)
uv run python scripts/publish-site.py --stage post-render

# Step 4: Optimize CSS and JS (must run AFTER render)
uv run python scripts/generate-fontawesome-subset.py --replace
uv run python scripts/generate-bootstrap-icons-subset.py --replace
uv run python scripts/purge-bootstrap-css-simple.py --replace
uv run python scripts/defer-javascript.py --replace
```

______________________________________________________________________

## Script Descriptions

### build-local.py

**Purpose**: Orchestrates a complete local build that mimics the GitHub Actions
workflow. Runs all render steps and CSS optimizations in the correct order.

**Location**: `scripts/build-local.py`

**Usage**:

```bash
# Full build (render + all optimizations) - SLOW, ~5 minutes
uv run python scripts/build-local.py

# Fast optimization-only mode (skip render) - FAST, ~30 seconds
uv run python scripts/build-local.py --skip-render
```

**Arguments**:

- `--skip-render` - Skip the slow quarto render step, only run CSS/JS optimizations

**What it does**:

**Without `--skip-render` (full build):**
1. **Render Stage** (SLOW): Runs `publish-site.py` with stages: all, render, post-render
   - Pre-render: Parse bibliography, minify files, copy files
   - Render: `quarto render` to build entire site (~5 minutes)
   - Post-render: Final cleanup steps
2. **Optimize Font Awesome CSS**: Runs `generate-fontawesome-subset.py --replace`
3. **Optimize Bootstrap Icons CSS**: Runs `generate-bootstrap-icons-subset.py --replace`
4. **Optimize Bootstrap CSS**: Runs `purge-bootstrap-css-simple.py --replace`
5. **Defer JavaScript**: Runs `defer-javascript.py --replace`

**With `--skip-render` (fast mode):**
1. ✅ Skip render (assumes `_site/` already exists)
2. **Optimize Font Awesome CSS**: Runs `generate-fontawesome-subset.py --replace`
3. **Optimize Bootstrap Icons CSS**: Runs `generate-bootstrap-icons-subset.py --replace`
4. **Optimize Bootstrap CSS**: Runs `purge-bootstrap-css-simple.py --replace`
5. **Defer JavaScript**: Runs `defer-javascript.py --replace`

**Output**:

- Colored progress indicators for each step
- Error messages if any step fails
- Success message with next steps for local testing

**When to use `--skip-render`**:

- ✅ Testing optimization scripts quickly
- ✅ Iterating on CSS/JS optimization changes
- ✅ You already have a recent `_site/` build
- ✅ You only changed optimization scripts, not content

**When to use full build** (without `--skip-render`):

- ✅ You edited `.qmd` content files
- ✅ You need a fresh build from scratch
- ✅ First-time setup or testing after pulling from GitHub

**Example workflows**:

```bash
# Workflow 1: Testing optimizations (FAST)
uv run python scripts/build-local.py --skip-render
cd _site && python3 -m http.server 8000
# Open http://localhost:8000 and check Lighthouse score

# Workflow 2: Content changes (SLOW)
vim blog/my-new-post.qmd
uv run python scripts/build-local.py  # No --skip-render
cd _site && python3 -m http.server 8000

# Workflow 3: Optimization script changes (FAST)
vim scripts/defer-javascript.py
uv run python scripts/build-local.py --skip-render
cd _site && python3 -m http.server 8000
```

______________________________________________________________________

### parse-bibliography.py

**Purpose**: Parses BibTeX bibliography files and generates Quarto markdown
pages for research papers and presentations.

**Location**: `scripts/parse-bibliography.py`

**Usage**:

```bash
uv run scripts/parse-bibliography.py [OPTIONS]
```

**Arguments**:

- `-b, --bibfile FILE` - Specify custom BibTeX file (default: `bibliography/bibtex/bibliography_kapfhammer.bib`)
- `-d, --delete` - Delete existing subdirectories in research/papers/ and research/presentations/
- `-f, --force` - Run even when not in full render mode

**What it does**:

1. Reads BibTeX entries from the bibliography file
1. Categorizes entries as papers or presentations
1. Generates individual Quarto `.qmd` files for each entry in:
   - `research/papers/<entry-key>/index.qmd`
   - `research/presentations/<entry-key>/index.qmd`
1. Extracts metadata (authors, title, venue, year, DOI, etc.)
1. Creates download links for PDFs and presentations
1. Applies keyword mapping for categorization

**When it runs**: Automatically during `quarto render` (pre-render phase) or
when called explicitly with `--force`.

**Output**: Generated `.qmd` files in research subdirectories that become
individual pages on the website.

______________________________________________________________________

### generate-fontawesome-subset.py

**Purpose**: Generates an optimized Font Awesome CSS file containing only the
icons actually used on the website, reducing file size from 135KB to ~2KB
(98.5% reduction).

**Location**: `scripts/generate-fontawesome-subset.py`

**Usage**:

```bash
# Local testing (safe mode - won't modify original)
uv run scripts/generate-fontawesome-subset.py

# CI/production (replaces original file)
uv run scripts/generate-fontawesome-subset.py --replace
```

**Arguments**:

- `--replace` - Replace `all.css` with the optimized subset (use in CI only)

**What it does**:

1. Scans all `.qmd`, `.yml`, and `.html` files for Font Awesome icon usage
1. Detects icons from multiple sources:
   - `{{< fa ... >}}` shortcodes
   - `{{< fa brands ... >}}` shortcodes
   - `{{< iconify fa6-solid ... >}}` shortcodes
   - `{{< iconify fa6-brands ... >}}` shortcodes
   - YAML `icon:` declarations
   - Direct HTML class attributes (`class="fa-solid fa-..."`)
1. Automatically categorizes icons as solid vs brand icons
1. Generates minimal CSS with only used icons
1. Writes to `all.subset.css` (safe mode) or replaces `all.css` (--replace mode)
1. Creates backup at `all.css.backup` when replacing

**Output files**:

- `_extensions/quarto-ext/fontawesome/assets/css/all.subset.css` (always)
- `_extensions/quarto-ext/fontawesome/assets/css/all.css` (only with --replace)
- `_extensions/quarto-ext/fontawesome/assets/css/all.css.backup` (backup)

**Current icons** (14 total):

- **Solid (9)**: book-open, circle-left, circle-up, copyright, file-pdf, highlighter, megaphone, rocket, rss
- **Brand (5)**: github, google, linkedin, mastodon, speaker-deck

**Adding new icons**:

1. Use the icon in your content (e.g., `{{< fa heart >}}`)
1. Add the icon's unicode to `ICON_CODES` dict in the script
1. Run the script - it will automatically detect and include the new icon

**When it runs**:

- Manually during local testing
- Automatically in GitHub Actions with `--replace` flag before deployment

______________________________________________________________________

### test-fontawesome-subset.py

**Purpose**: Automated testing for Font Awesome optimization to ensure all icons
are properly included and working.

**Location**: `scripts/test-fontawesome-subset.py`

**Usage**:

```bash
python scripts/test-fontawesome-subset.py
```

**Arguments**: None

**What it does**:

1. Checks CSS file size (should be ~2KB, not 135KB)
1. Scans HTML files for icon usage
1. Verifies all HTML icons are defined in CSS
1. Checks for font-face declarations
1. Provides manual testing checklist

**Tests performed**:

- ✅ CSS file size validation
- ✅ Icon coverage (HTML vs CSS)
- ✅ Font-face declarations present
- ✅ WOFF2 font references
- ✅ font-display: swap optimization

**When it runs**: Manually after running `generate-fontawesome-subset.py` and
`quarto render` to verify the optimization worked correctly.

______________________________________________________________________

### generate-bootstrap-icons-subset.py

**Purpose**: Generates an optimized Bootstrap Icons CSS file containing only the
icons actually used on the website, reducing file size from 96KB to ~1KB
(98.9% reduction).

**Location**: `scripts/generate-bootstrap-icons-subset.py`

**Usage**:

```bash
# Local testing (safe mode - won't modify original)
uv run scripts/generate-bootstrap-icons-subset.py

# CI/production (replaces original file)
uv run scripts/generate-bootstrap-icons-subset.py --replace
```

**Arguments**:

- `--replace` - Replace `bootstrap-icons.css` with the optimized subset (use in
  CI only)

**What it does**:

1. Scans all HTML files in `_site` for Bootstrap Icons usage
1. Detects icons from class attributes (`class="bi bi-github"`)
1. Checks `_quarto.yml` for icon declarations in navbar/footer
1. Generates minimal CSS with only used icons
1. Writes to `bootstrap-icons.subset.css` (safe mode) or replaces
   `bootstrap-icons.css` (--replace mode)
1. Creates backup at `bootstrap-icons.css.backup` when replacing
1. Handles read-only file permissions set by Quarto

**Output files**:

- `_site/site_libs/bootstrap/bootstrap-icons.subset.css` (always)
- `_site/site_libs/bootstrap/bootstrap-icons.css` (only with --replace)
- `_site/site_libs/bootstrap/bootstrap-icons.css.backup` (backup)

**Current icons** (8 total):

- github, google, linkedin, mastodon, megaphone, search, sort-down, x-lg

**Adding new icons**:

1. Use the icon in your Quarto config (e.g., `icon: twitter` in navbar)
1. Find the icon's unicode at https://icons.getbootstrap.com/
1. Add to `ICON_CODES` dict in the script
1. Run the script - it will automatically detect and include the new icon

**When it runs**:

- Manually during local testing (after `quarto render`)
- Automatically in GitHub Actions with `--replace` flag after rendering

**Note**: This script must run AFTER `quarto render` because Quarto generates
the `bootstrap-icons.css` file during the render process.

______________________________________________________________________

### purge-bootstrap-css-simple.py

**Purpose**: Optimizes Bootstrap CSS files by removing unused CSS classes and
rules, reducing file size from 997KB to ~157KB (84% reduction).

**Location**: `scripts/purge-bootstrap-css-simple.py`

**Usage**:

```bash
# Local testing (safe mode - won't modify original)
uv run scripts/purge-bootstrap-css-simple.py

# CI/production (replaces original files)
uv run scripts/purge-bootstrap-css-simple.py --replace
```

**Arguments**:

- `--replace` - Replace original Bootstrap CSS files with optimized versions
  (use in CI only)

**What it does**:

1. Locates Bootstrap CSS files in `_site/site_libs/bootstrap/`:
   - `bootstrap-*.min.css` (light theme)
   - `bootstrap-dark-*.min.css` (dark theme)
2. Uses PurgeCSS (via npx) to remove unused CSS classes
3. Scans all HTML and JS files in `_site` to determine which classes are used
4. Automatically detects which Bootstrap classes are needed (no manual safelist)
5. Writes to `.purged.css` files (safe mode) or replaces originals (--replace mode)
6. Creates backup files with `.backup` extension when replacing

**Output files**:

- `_site/site_libs/bootstrap/bootstrap-*.min.css.purged` (always)
- `_site/site_libs/bootstrap/bootstrap-dark-*.min.css.purged` (always)
- `_site/site_libs/bootstrap/bootstrap-*.min.css` (only with --replace)
- `_site/site_libs/bootstrap/bootstrap-dark-*.min.css` (only with --replace)
- `_site/site_libs/bootstrap/*.backup` (backup files)

**Performance impact**:

- Light theme: 498KB → 78KB (84% reduction)
- Dark theme: 500KB → 80KB (84% reduction)
- Total savings: ~839KB

**PurgeCSS configuration**:

The script uses PurgeCSS with these settings:
- Content sources: All HTML and JS files in `_site/`
- No manual safelist (auto-detection only)
- Preserves keyframes and font-face rules
- Handles dynamic class names via regex patterns

**When it runs**:

- Manually during local testing (after `quarto render`)
- Automatically in GitHub Actions with `--replace` flag after rendering

**Note**: This script must run AFTER `quarto render` because Quarto generates
the Bootstrap CSS files during the render process. It requires Node.js and npx
to be installed (for running PurgeCSS).

______________________________________________________________________

### defer-javascript.py

**Purpose**: Adds `defer` attribute to script tags in HTML files to prevent
render-blocking JavaScript, significantly improving Lighthouse performance scores
(+10-15 points expected).

**Location**: `scripts/defer-javascript.py`

**Usage**:

```bash
# Local testing (safe mode - won't modify original)
uv run scripts/defer-javascript.py

# CI/production (replaces original files)
uv run scripts/defer-javascript.py --replace
```

**Arguments**:

- `--replace` - Replace original HTML files with optimized versions (use in CI only)

**What it does**:

1. Scans all HTML files in `_site/` directory
2. Finds all `<script>` tags with `src` attributes (external scripts)
3. Adds `defer` attribute to eligible scripts
4. Skips scripts that should NOT be deferred:
   - Scripts with `type="application/json"` (configuration data)
   - Scripts with `type="module"` (already deferred by browsers)
   - Critical inline scripts (DOM-ready handlers, color scheme toggles)
   - Scripts that already have `defer` or `async` attributes
5. Creates backup files with `.backup-defer` extension when replacing

**How `defer` works**:

- **Without defer**: Browser downloads and executes JS immediately, blocking HTML parsing
- **With defer**: Browser downloads JS in parallel with HTML parsing, executes after DOM is ready
- **Result**: Page renders faster, improves First Contentful Paint (FCP) and Largest Contentful Paint (LCP)

**Performance impact**:

- Expected Lighthouse performance score improvement: **+10-15 points**
- Improves Time to Interactive (TTI) and Total Blocking Time (TBT)
- Scripts still execute in order and have access to full DOM

**Scripts that get deferred**:

- Bootstrap.min.js (79KB)
- jQuery (from CDN)
- quarto-nav.js, quarto-listing.js
- All Quarto helper libraries (popper, tippy, anchor, etc.)

**When it runs**:

- Manually during local testing (after `quarto render`)
- Automatically in GitHub Actions with `--replace` flag after all CSS optimizations

**Why this must be a script**:

Quarto doesn't provide built-in options to add `defer` attributes to its generated
script tags. This script modifies the HTML output AFTER Quarto renders to add the
optimization while preserving all functionality.

**Note**: This script must run AFTER `quarto render` because it modifies the HTML
files that Quarto generates.

______________________________________________________________________

### minify-files.py

**Purpose**: Minifies HTML, CSS, and JavaScript files in the rendered `_site`
directory to reduce file sizes and improve page load performance.

**Location**: `scripts/minify-files.py`

**Usage**:

```bash
uv run scripts/minify-files.py [OPTIONS]
```

**Arguments**:

- `-s, --source DIR` - Source directory (default: `_site`)
- `-d, --destination DIR` - Destination directory (default: `_site`)
- `-f, --force` - Run even when not in full render mode
- `-v, --verbose` - Display detailed progress information

**What it does**:

1. Creates timestamped backup of destination directory (`_site_backup_TIMESTAMP`)
1. Recursively processes all files in source directory
1. Minifies files based on extension:
   - **CSS**: Uses `csscompressor` to remove whitespace and comments
   - **HTML**: Uses `minify_html` with JS/CSS minification enabled
   - **JS**: Uses `rjsmin` for JavaScript minification
1. Displays size reduction statistics for each file
1. Preserves file permissions and timestamps

**Performance impact**:

- CSS: Typically 20-40% reduction
- HTML: Typically 10-30% reduction
- JS: Typically 30-50% reduction

**When it runs**: Part of the post-render phase, called by `publish-site.py` or
run manually for local testing.

**Note**: Creates backups before modifying files. Skips files that cannot be
minified and continues processing.

______________________________________________________________________

### copy-files.py

**Purpose**: Copies research paper and presentation PDFs from resource
directories to the rendered site directory.

**Location**: `scripts/copy-files.py`

**Usage**:

```bash
uv run scripts/copy-files.py [OPTIONS]
```

**Arguments**:

- `-s, --source DIR` - Source directory
- `-d, --destination DIR` - Destination directory
- `-f, --force` - Run even when not in full render mode

**Default copy operations**:

1. Papers: `_resources/download/research/papers/key/*.pdf` → `_site/download/research/papers/key/`
1. Presentations: `_resources/download/research/presentations/key/*.pdf` → `_site/download/research/presentations/key/`

**What it does**:

1. Checks for `QUARTO_PROJECT_RENDER_ALL` environment variable (unless --force)
1. If no arguments: performs default copies for papers and presentations
1. If -s and -d provided: copies files from source to destination
1. Creates destination directories if they don't exist
1. Uses `shutil.copy2()` to preserve file metadata
1. Reports count of files copied

**When it runs**: Part of the post-render phase, called by `publish-site.py` or
when PDFs need to be synced to the rendered site.

______________________________________________________________________

### publish-site.py

**Purpose**: Orchestrates the entire build and publish workflow by calling other
scripts in the correct order and publishing to hosting platforms.

**Location**: `scripts/publish-site.py`

**Usage**:

```bash
uv run scripts/publish-site.py --stages STAGE [STAGE ...]
```

**Arguments**:

- `-s, --stages STAGES` - One or more stages to execute (see below)
- `-p, --use-poetry-venv` - Use Poetry virtual environment (legacy)
- `-r, --render-file FILE` - Render only a specific file

**Available stages**:

- `pre-render` - Run parse-bibliography.py
- `render` - Run quarto render
- `minify` - Run minify-files.py (part of post-render)
- `copy` - Run copy-files.py (part of post-render)
- `post-render` - Run both minify and copy
- `quarto-pub` - Publish to Quarto Pub
- `netlify` - Publish to Netlify
- `publish` - Publish to configured host
- `all` - Run all stages in order

**Stage execution order**:

1. **pre-render**: Parse bibliography → generate research pages
1. **render**: Quarto renders all .qmd files to HTML
1. **post-render**:
   - **minify**: Compress HTML/CSS/JS files
   - **copy**: Move PDFs to site directory
1. **publish**: Deploy to hosting platform

**Common usage patterns**:

```bash
# Full build and local preview
uv run scripts/publish-site.py --stages all

# Just pre-render and render
uv run scripts/publish-site.py --stages pre-render render

# Post-render optimization only
uv run scripts/publish-site.py --stages post-render

# Full build and publish to Netlify
uv run scripts/publish-site.py --stages all netlify

# Render single file
uv run scripts/publish-site.py --stages render --render-file index.qmd
```

**When it runs**: Manually when you want to orchestrate multiple build steps in
a single command.

______________________________________________________________________

## Build Pipeline

Here's how the scripts work together in the complete build process:

### Local Development

```
1. Edit content (.qmd files)
   ↓
2. quarto preview (live preview, scripts don't run)
   ↓
3. Review changes
```

### Full Local Build (Recommended)

**Using the build-local.py script** (easiest method):

```
1. uv run python scripts/build-local.py
   ├─ Pre-render: parse-bibliography.py generates research pages
   ├─ Render: quarto render builds entire site
   ├─ Post-render: minify-files.py and copy-files.py
   ├─ Optimize Font Awesome CSS (135KB → 2KB)
   ├─ Optimize Bootstrap Icons CSS (96KB → 1KB)
   ├─ Optimize Bootstrap CSS (997KB → 157KB)
   └─ Defer JavaScript (prevent render-blocking)
   ↓
2. cd _site && python3 -m http.server 8000
   └─ Test at http://localhost:8000
```

**Fast mode** (if `_site/` already exists):

```
1. uv run python scripts/build-local.py --skip-render
   ├─ Skip slow render (use existing _site/)
   ├─ Optimize Font Awesome CSS (135KB → 2KB)
   ├─ Optimize Bootstrap Icons CSS (96KB → 1KB)
   ├─ Optimize Bootstrap CSS (997KB → 157KB)
   └─ Defer JavaScript (prevent render-blocking)
   ↓
2. cd _site && python3 -m http.server 8000
   └─ Test at http://localhost:8000
```

**Manual steps** (if you need fine-grained control):

```
1. uv run scripts/publish-site.py --stages pre-render
   └─ parse-bibliography.py generates research pages
   ↓
2. uv run scripts/publish-site.py --stages render
   └─ quarto render builds entire site
   ↓
3. uv run scripts/generate-fontawesome-subset.py --replace
   └─ optimize Font Awesome CSS (must run after render)
   ↓
4. uv run scripts/generate-bootstrap-icons-subset.py --replace
   └─ optimize Bootstrap Icons CSS (must run after render)
   ↓
5. uv run scripts/purge-bootstrap-css-simple.py --replace
   └─ optimize Bootstrap CSS (must run after render)
   ↓
6. uv run scripts/defer-javascript.py --replace
   └─ add defer attributes to script tags (must run after render)
   ↓
7. uv run scripts/publish-site.py --stages post-render
   ├─ minify-files.py compresses HTML/CSS/JS
   └─ copy-files.py moves PDFs to _site
```

### GitHub Actions (CI/CD)

```
1. Checkout code
   ↓
2. Install uv and dependencies
   └─ uv sync
   ↓
3. Pre-render and Render
   └─ uv run scripts/publish-site.py (all stages)
   ↓
4. Optimize Font Awesome CSS
   └─ uv run scripts/generate-fontawesome-subset.py --replace
   ↓
5. Optimize Bootstrap Icons CSS
   └─ uv run scripts/generate-bootstrap-icons-subset.py --replace
   ↓
6. Optimize Bootstrap CSS
   └─ uv run scripts/purge-bootstrap-css-simple.py --replace
   ↓
7. Defer JavaScript Loading
   └─ uv run scripts/defer-javascript.py --replace
   ↓
8. Deploy to Cloudflare Pages
   └─ wrangler pages deploy
```

**Total Optimizations**: ~1,070 KB CSS saved + render-blocking JS eliminated

- Font Awesome: 133 KB saved (98.5% reduction)
- Bootstrap Icons: 95 KB saved (98.9% reduction)
- Bootstrap CSS: 839 KB saved (84% reduction)
- JavaScript: Defer attribute added (improves Lighthouse +10-15 points)

______________________________________________________________________

## Common Patterns

### Environment Detection

Most scripts check if they're running in a full render:

```python
if not os.getenv("QUARTO_PROJECT_RENDER_ALL") and not args.force:
    sys.exit()
```

This prevents scripts from running during `quarto preview`, which would slow
down the development workflow.

### Force Flag

Override environment detection for testing:

```bash
uv run scripts/copy-files.py --force
```

### Rich Console Output

All scripts use Rich for formatted output:

```python
from rich.console import Console

console = Console()
console.print(":tada: Task completed!", style="bold blue")
```

### UV Integration

Scripts access project dependencies via `uv run`:

```bash
uv run scripts/script-name.py
```

This ensures the correct Python environment with all required packages
(rich, bibtexparser, csscompressor, etc.) is used.

______________________________________________________________________

## Adding New Scripts

When creating new scripts, follow these conventions:

1. **Imports**: Use `from rich.console import Console` for output
1. **Arguments**: Use `argparse` with `-f/--force` flag
1. **Environment**: Check `QUARTO_PROJECT_RENDER_ALL` unless forced
1. **Documentation**: Add docstring explaining purpose and usage
1. **Integration**: Update this README with script details
1. **Dependencies**: Add to `pyproject.toml` if new packages needed

______________________________________________________________________

## Troubleshooting

### Script won't run during preview

This is expected behavior. Use `--force` flag for testing:

```bash
uv run scripts/script-name.py --force
```

### ModuleNotFoundError

Make sure to run scripts with `uv run`:

```bash
uv run scripts/script-name.py
```

### Scripts running too slow

Scripts are designed for full builds, not preview mode. During development, use
`quarto preview` which skips script execution.

### File permission errors

Some scripts (like minify-files.py) modify file permissions. Ensure you have
write access to the target directories.

______________________________________________________________________

## Questions or Issues?

For questions about these scripts or to report issues:

- Review the script's docstring and inline comments
- Check the GitHub Actions workflow for usage examples
- Open an issue on the repository
