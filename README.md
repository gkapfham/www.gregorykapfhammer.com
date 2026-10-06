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

### Preview Options for Concurrent Editing

Quarto allows one preview server per project directory. The `--port` option
selects the HTTP port, but it does not allow multiple preview processes for the
same project. Quarto uses the following project-specific lock file:

```text
.quarto/preview/lock
```

Consequently, starting a second preview from this directory terminates the
first one and prints `Terminating existing preview server....DONE`. Do not
remove this lock file manually: doing so can leave multiple processes writing
to the same Quarto state and generated files.

The recommended workflow when several processes are editing this site is to
run one shared preview server:

```bash
quarto preview --port 5556 --no-browser --no-navigate
```

The options have these meanings:

- `--port 5556` selects the local HTTP port.
- `--no-browser` prevents Quarto from opening a new browser window.
- `--no-navigate` prevents Quarto from switching the browser to the page whose
  source file was most recently changed.

The `--no-navigate` option is important when reviewing one page while another
process edits a different page. The current page remains open, while Quarto
continues to rebuild changed inputs. All editing processes can use the same
URL, `http://localhost:5556/`.

Do not use `--no-watch-inputs` for this shared live-preview workflow. That
option disables automatic input rebuilding; it is useful only when the output
should remain unchanged until a manual render. For example:

```bash
quarto preview --port 5556 --no-browser --no-navigate \
  --no-watch-inputs
```

If separate, isolated previews are required, use separate ordinary temporary
copies of the project. A Git worktree is not required:

```bash
preview_dir="$(mktemp -d /tmp/www-preview.XXXXXX)"
rsync -a --delete \
  --exclude='.git' \
  --exclude='.quarto' \
  --exclude='_site' \
  ./ "$preview_dir/"

cd "$preview_dir"
quarto preview --port 5557 --no-browser --no-navigate
```

This copy is a snapshot. Repeat the `rsync` command when the source directory
changes if the isolated preview should receive later edits. Each copy has its
own project directory, `.quarto` state, preview lock, and generated output.

When only already-rendered HTML needs to be inspected, no Quarto preview
process is necessary:

```bash
python -m http.server 8000 --directory _site
```

This serves the current `_site` directory without changing it. It is useful
for inspecting a completed render, but it does not rebuild the site when QMD
files change.

Changing `--port`, selecting a Quarto `--profile`, or setting a different
`--output-dir` does not by itself create a second project lock. Use one shared
preview server, a separate project copy, or a separate Git worktree when two
independent Quarto preview processes are genuinely needed.

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

### Verifying the research timelines

The research overview, the papers page, and the presentations page each draw a
publication timeline: one dot per paper or presentation on a year axis. The tool
in `_tools/verify-timelines.py` re-derives what every timeline must contain from
the front matter of the papers and the presentations, so it fails whenever an
entry is added, removed, or re-dated without the timeline being regenerated. An
area timeline also draws the papers that its paragraph cites but that the
area's listing filter does not hold; those related dots are drawn hollow, and
the caption counts and links only the area's own tagged papers.

It checks that each timeline draws one dot per expected entry and no others,
that every dot links to an entry that exists and carries that entry's year,
that the marks advance with the years and span the whole axis, that the caption
counts the entries and names the first year, that the axis labels cover the
first and last year, that a caption links a listing filter only when the rail
matches that filter exactly, that the raw HTML stays inside 80 columns, and that
Quarto did not turn the nested HTML into a code block.

```bash
# verify every timeline: the overview, the papers, and the presentations
uv run _tools/verify-timelines.py

# verify a single page
uv run _tools/verify-timelines.py --target papers
uv run _tools/verify-timelines.py --target presentations

# also inspect the rendered HTML under a build directory, which is what a
# browser downloads, and confirm that every dot points at a page that was built
uv run _tools/verify-timelines.py --site _site

# print only the summary and any problems
uv run _tools/verify-timelines.py --quiet
```

The command exits with 0 when every timeline matches its sources and with 1 when
any check fails, so it can be used in a build step or a shell script.

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
