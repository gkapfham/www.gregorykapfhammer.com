# www.gregorykapfhammer.com

## Introduction

This is the website of Gregory M. Kapfhammer, built with
[Quarto](https://quarto.org/). The site is automatically deployed to Cloudflare
Pages via GitHub Actions whenever changes are pushed to the `master` branch.

## Local Development

### Quick Preview

For rapid iteration during content development:

```bash
quarto preview
```

This starts a live preview server without running any build scripts or
optimizations.

### Full Local Build

To build the site with all CSS optimizations (mimics production deployment):

```bash
# Run the local build script
uv run python scripts/build-local.py

# Test locally
cd _site
python -m http.server 8000
```

Then open `http://localhost:8000` in your browser.

## Build Scripts

This repository includes Python scripts for building, optimizing, and deploying
the website. These scripts handle bibliography parsing, CSS optimization, file
minification, and deployment.

**See [scripts/README.md](scripts/README.md) for complete documentation of all
available scripts.**

### Key Scripts

- **`build-local.py`** - Complete local build with all optimizations (recommended)
- **`publish-site.py`** - Orchestrates build stages (pre-render, render, post-render)
- **`parse-bibliography.py`** - Generates research pages from BibTeX files
- **`generate-fontawesome-subset.py`** - Optimizes Font Awesome CSS (135KB → 2KB)
- **`generate-bootstrap-icons-subset.py`** - Optimizes Bootstrap Icons CSS (96KB → 1KB)
- **`purge-bootstrap-css-simple.py`** - Optimizes Bootstrap CSS (997KB → 157KB)

## Deployment

The site is automatically deployed via GitHub Actions when you push to `master`.
The workflow runs all build steps and CSS optimizations before deploying to
Cloudflare Pages.

**See `.github/workflows/publish.yml` for the complete CI/CD pipeline.**

## Requirements

- **Quarto** 1.7.31 or later
- **Python** 3.14 with `uv` package manager
- **Node.js** and `npx` (for PurgeCSS)

All Python dependencies are managed by `uv` and defined in `pyproject.toml`.
