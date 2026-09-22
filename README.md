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

## Software Engineering Radio Blog Posts

Two tools in `_tools/` support the posts about episodes of the Software
Engineering Radio podcast. Both write transcripts to a cache outside of this
repository, in `~/.cache/seradio-transcripts`, so the published text of an
episode is never committed. Both also trim the site navigation that follows
the transcript on the episode page, so a cached transcript holds the
transcript alone.

### Fetching a transcript

`_tools/fetch-seradio-transcript.py` downloads the transcript of an episode
and reports the details that a post needs: the episode number, the title, the
number of speaker turns, and the URL of the MP3 file along with a ready to
paste Quarto audio shortcode. Run it as soon as an episode is published, even
before the post exists, and then search the cached transcript while writing.

```bash
# fetch a transcript, cache it, and report the details of the episode
uv run _tools/fetch-seradio-transcript.py --url <episode-page-url>

# search a transcript without writing a file, because the report goes to
# standard error while the transcript goes to standard output
uv run _tools/fetch-seradio-transcript.py --url <episode-page-url> --stdout \
    | grep -i mutation

# write a transcript to another path and replace an existing copy
uv run _tools/fetch-seradio-transcript.py --url <episode-page-url> \
    --output /tmp/726-transcript.txt --force

# list the transcripts that are already cached
uv run _tools/fetch-seradio-transcript.py --list
```

### Verifying a post

Posts about episodes quote the guest directly, so
`_tools/verify-seradio-post.py` checks a post against the transcript that
Software Engineering Radio publishes. The tool enforces the rules in
[AGENTS.md](AGENTS.md): every quotation must appear verbatim in the
transcript, the prose must fit in 80 columns, the front matter and the
required sections must be present, and no emoji may be used. It can also
fetch every link in the post and report the status of each one.

Run this tool after writing or editing a `blog/se-radio-<slug>/index.qmd`
file and before committing the change. Neither the local build nor the GitHub
Actions workflow checks these posts, so this tool provides the only
verification that they receive.

```bash
# verify a post against a transcript in the cache
uv run _tools/verify-seradio-post.py \
    --post blog/se-radio-jeroen-janssens-thijs-nieuwdorp-polars/index.qmd \
    --episode 727

# download the transcript first when the cache is empty, then verify
uv run _tools/verify-seradio-post.py --post <post> --episode 726 --fetch \
    --url <episode-page-url>

# verify the post and fetch every link that it contains
uv run _tools/verify-seradio-post.py --post <post> --episode 727 --check-links

# also reject lines that exceed 80 columns because of a long URL
uv run _tools/verify-seradio-post.py --post <post> --episode 727 \
    --strict-width
```

The tool exits with 0 when every check passes and 1 when a check fails, so it
can be used in a pre-commit hook or a shell script. Its report is rendered
with [Rich](https://rich.readthedocs.io/) and shows a table that pairs each
quotation with the speaker and the timestamp of the transcript turn that
contains it. That table is the supporting evidence that
[AGENTS.md](AGENTS.md) asks the writing agent to produce.

The tools live in `_tools/`, a directory that Quarto ignores because its name
starts with an underscore, so they are never rendered or deployed.

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
