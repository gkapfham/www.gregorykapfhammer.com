"""Regenerate the publication timelines that the research pages draw.

The timelines are raw HTML blocks that the research overview, the papers
page, and the presentations page each carry. This tool rebuilds those
blocks from the front matter of the papers and the presentations, using
the same membership rules as _tools/verify-timelines.py, so the two tools
can never disagree about which papers belong to an area.

Run it with --check first: that reports which timelines would change and
writes nothing. Without --check it rewrites the blocks in place.

    uv run _tools/generate-timelines.py --check
    uv run _tools/generate-timelines.py

The shape of a timeline:

  * one dot per paper or presentation, grouped by the year it was published
  * the marks are placed proportionally for a whole-career rail and with a
    minimum gap for an area rail, which keeps tightly clustered years apart
  * five or six years are labelled on the axis, starting and ending with the
    first and last year
  * the caption carries a timeline icon, the number of entries, the area
    label, and the first year, and it links to a listing filter only when
    the rail draws exactly the papers in that filter
"""

import argparse
import importlib.util
import pathlib
import re
import sys
from dataclasses import dataclass
from typing import Sequence

from rich.console import Console

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
AREAS_PAGE = REPO_ROOT / "research" / "index.qmd"
PAPERS_PAGE = REPO_ROOT / "research" / "papers" / "index.qmd"
TALKS_PAGE = REPO_ROOT / "research" / "presentations" / "index.qmd"
MAX_COLUMN = 80
MAX_LABELS = 6
MIN_MARK_GAP = 14.0
AXIS_MAX_PERCENT = 100.0
MAX_LABEL_CHARS = 42
MIN_LABEL_CHARS = 6
TALL_STACK = 6
BLOCK_RE = re.compile(r"```\{=html\}\n(.*?)\n```", re.S)
FIGURE_RE = re.compile(r'<figure class="pub-timeline[^"]*">.*?</figure>', re.S)


@dataclass
class Rail:
    """How one timeline is built."""

    label: str
    category: str | None = None
    career: bool = False
    word: str = "papers"
    dot_prefix: str = "/research/papers/"


STOPWORDS = {
    "and",
    "or",
    "the",
    "a",
    "an",
    "of",
    "for",
    "with",
    "to",
    "on",
    "in",
    "at",
    "by",
    "from",
    "that",
    "which",
    "using",
}
ICON = '<iconify-icon inline icon="fa6-solid:timeline"></iconify-icon>'
CAREER_LABEL = "software engineering and software testing"

console = Console()

# reuse the verifier so the membership rules live in exactly one place
_spec = importlib.util.spec_from_file_location(
    "verify_timelines", REPO_ROOT / "_tools" / "verify-timelines.py"
)
verifier = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(verifier)


def positions(years: Sequence[int], min_gap: float) -> list[float]:
    """Place the years on the axis, optionally with a minimum gap."""
    first, last = years[0], years[-1]
    span = max(1, last - first)
    out: list[float] = []
    for index, year in enumerate(years):
        raw = (year - first) / span * 100.0
        out.append(raw if index == 0 else max(raw, out[-1] + min_gap))
    if out[-1] > AXIS_MAX_PERCENT:
        scale = 100.0 / out[-1]
        out = [value * scale for value in out]
    return [round(value, 1) for value in out]


def label_years(years: Sequence[int], pct: Sequence[float]) -> set[int]:
    """Label at most six years, spread across the axis."""
    if len(years) <= MAX_LABELS:
        return set(years)
    targets = [0, 20, 40, 60, 80, 100][:MAX_LABELS]
    chosen: list[int] = []
    for target in targets:
        best = min(
            (pair for pair in zip(years, pct) if pair[0] not in chosen),
            key=lambda pair: abs(pair[1] - target),
        )
        chosen.append(best[0])
    return set(chosen)


def short_label(title: str) -> str:
    """A short label for a dot tooltip."""
    head, sep, _ = title.partition(":")
    if sep and MIN_LABEL_CHARS <= len(head) <= MAX_LABEL_CHARS:
        return head.strip()
    words: list[str] = []
    for word in title.split():
        if len(" ".join([*words, word])) > MAX_LABEL_CHARS:
            break
        words.append(word)
    # a tooltip that ends on a preposition or article reads badly
    while words and words[-1].lower().strip(",.;:") in STOPWORDS:
        words.pop()
    return " ".join(words) if words else title[:MAX_LABEL_CHARS]


def caption_tokens(count: int, word: str, label: str, year: int, linked: bool):
    """Build the caption pieces in the site's format."""
    tail = "</span>" + ("</a>" if linked else "")
    return [
        '<span class="pt-count">' + str(count) + " " + word + "</span>",
        "on",
        "<span",
        'class="pt-category">' + label + "</span>",
        "published",
        "since",
        "<span",
        'class="pt-category">' + str(year) + tail,
    ]


def wrap(opening: str, tokens: Sequence[str], limit: int = 78) -> list[str]:
    """Lay the caption out, one token at a time."""
    opening_lines = opening.split("\n")
    lines = list(opening_lines[:-1])
    current = opening_lines[-1]
    for token in tokens:
        if len(current) + 1 + len(token) > limit:
            lines.append(current)
            current = " " + token
        else:
            current = current + " " + token
    lines.append(current)
    lines.append("</figcaption>")
    return lines


def build(entries, rail: Rail) -> str:
    """Return the HTML figure for one timeline (without the code fences)."""
    entries = sorted(entries, key=lambda entry: (entry.year, entry.slug))
    years = sorted({entry.year for entry in entries})
    pct = positions(years, 0.0 if rail.career else MIN_MARK_GAP)
    labelled = label_years(years, pct)
    by_year: dict[int, list] = {}
    for entry in entries:
        by_year.setdefault(entry.year, []).append(entry)

    classes = "pub-timeline" + (" pt-career" if rail.career else "")
    if max(len(by_year[year]) for year in years) >= TALL_STACK:
        classes += " pt-tall"

    opening = "<figcaption>" + ICON
    if rail.category:
        opening += '\n<a href="/research/papers/#category=' + rail.category + '">'
    lines = [f'<figure class="{classes}">']
    lines += wrap(
        opening,
        caption_tokens(
            len(entries), rail.word, rail.label, years[0], bool(rail.category)
        ),
    )
    lines += [
        '<div class="pt-rail">',
        '<div class="pt-track">',
        '<span class="pt-line" aria-hidden="true"></span>',
    ]

    for index, (year, position) in enumerate(zip(years, pct)):
        mark = "pt-mark"
        if index == 0:
            mark += " pt-first"
        if year == years[-1]:
            mark += " pt-latest pt-last"
        lines.append(f'<span class="{mark}" style="--pt: {position};">')
        lines.append('<span class="pt-stack">')
        for entry in by_year[year]:
            dot = short_label(entry.title)
            lines.append(f'<a class="pt-dot" href="{rail.dot_prefix}{entry.slug}/"')
            lines.append(f' aria-label="{entry.slug}: {dot}"')
            lines.append(f' title="{year} &middot; {dot}"></a>')
        lines.append("</span>")
        if year in labelled:
            lines.append(f'<span class="pt-year">{year}</span>')
        lines.append("</span>")

    lines += ["</div>", "</div>", "</figure>"]
    for line in lines:
        if len(line) > MAX_COLUMN:
            raise SystemExit(f"line too long ({len(line)}): {line}")
    return "\n".join(lines)


def linked_filter(current: str, entries, members: dict[str, set[str]]) -> str | None:
    """Return the filter that a caption may link, or None when it may not.

    A caption may link a listing filter only when the rail draws exactly the
    papers in that filter. Every area rail also carries the papers that its
    paragraph cites, so an area whose paragraph reaches outside its own
    category no longer links the filter.
    """
    link = verifier.LINK_RE.search(current)
    if not link:
        return None
    raw = link.group(1).partition("#category=")[2]
    name = raw.replace("%20", " ")
    rail = {entry.slug for entry in entries}
    return raw if members.get(name) == rail else None


def area_blocks(papers) -> list[tuple[str, str, str]]:
    """Return (page, heading, block) for every area timeline."""
    page = verifier.relative_path(AREAS_PAGE)
    by_identifier = {entry.identifier: entry for entry in papers}
    members = verifier.load_category_members(REPO_ROOT / "research" / "papers")
    out = []
    text = AREAS_PAGE.read_text()
    for part in verifier.page_sections(text):
        heading_match = re.search(r"^### (.+)$", part, re.M)
        if not heading_match:
            continue
        heading = heading_match.group(1).strip()
        block = verifier.BLOCK_RE.findall(part)
        current = block[0] if block else ""
        entries = verifier.area_entries(heading, part, papers, by_identifier)
        rule = verifier.AREA_RULES.get(heading, {})
        label = rule.get("category", heading.lower())
        category = linked_filter(current, entries, members)
        out.append(
            (page, heading, build(entries, Rail(label=label, category=category)))
        )
    return out


def write_page(path: pathlib.Path, blocks: Sequence[str], check: bool) -> int:
    """Replace the timeline figures of one page, in document order."""
    text = path.read_text()
    figures = FIGURE_RE.findall(text)
    if len(figures) != len(blocks):
        raise SystemExit(
            f"{path}: found {len(figures)} timelines for {len(blocks)} generated blocks"
        )
    changed = 0
    for current, block in zip(figures, blocks):
        if current == block:
            continue
        changed += 1
        if not check:
            text = text.replace(current, block, 1)
    if changed and not check:
        path.write_text(text)
    return changed


def main(argv=None) -> int:
    """Regenerate the timelines, or report what would change."""
    parser = argparse.ArgumentParser(
        description="Regenerate the publication timelines.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="report what would change and write nothing",
    )
    args = parser.parse_args(argv)

    papers = verifier.load_entries(REPO_ROOT / "research" / "papers")
    talks = verifier.load_entries(REPO_ROOT / "research" / "presentations")

    area_blocks_only = [block for _, _, block in area_blocks(papers)]
    jobs = [
        ("research/index.qmd", area_blocks_only),
        ("research/papers/index.qmd", [build(papers, Rail(CAREER_LABEL, career=True))]),
        (
            "research/presentations/index.qmd",
            [
                build(
                    talks,
                    Rail(
                        CAREER_LABEL, career=True, word="presentations", dot_prefix=""
                    ),
                )
            ],
        ),
    ]
    total = 0
    for page, blocks in jobs:
        path = REPO_ROOT / page
        changed = write_page(path, blocks, args.check)
        total += changed
        state = (
            "unchanged"
            if not changed
            else ("would change" if args.check else "rewritten")
        )
        console.print(f"{page}: {len(blocks)} timeline(s), {state}")
    console.print(f"{'would rewrite' if args.check else 'rewrote'} {total} timeline(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
