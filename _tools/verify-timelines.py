"""Verify the publication timelines that the research pages display.

Currently, three pages carry a timeline: the research overview has one per
research area, the papers page has one that covers every paper, and the
presentations page has one that covers every presentation. Each timeline is a
Quarto raw HTML block that draws one dot per entry on a year axis.

The tool re-derives what a timeline must contain from the front matter
of the papers and the presentations themselves and then checks the
markup against that expectation. It therefore fails when an entry is
added, removed, or re-dated without the timeline being regenerated.

Checks, for every timeline:

  * one dot per expected entry, and no dot for an entry that is absent
  * every dot links to a directory that holds an index.qmd
  * the year in each dot title matches the year of that entry
  * the marks sit at the positions that the entry years imply
  * the caption counts the entries and names the first year
  * the axis labels are real years and they start and end the axis
  * a linked caption names a category that the listing really has
  * the raw HTML block stays inside 80 columns
  * pandoc did not turn the nested HTML into a code block

With --site the tool also inspects the rendered HTML under a build
directory, which is what a browser downloads, and it confirms that
every dot points at a page that was actually built.

Run the tool through uv run so that the project interpreter and the
dependencies in pyproject.toml are used::

    uv run _tools/verify-timelines.py
    uv run _tools/verify-timelines.py --target papers
    uv run _tools/verify-timelines.py --site _site

The report is rendered with rich, which is already declared in
pyproject.toml. rich is used rather than the built-in print because the
repository's ruff configuration selects T201 (flake8-print). See
README.md for how and when to use this tool.
"""

import argparse
import itertools
import pathlib
import re
import sys
from dataclasses import dataclass, field
from typing import Sequence

from rich.console import Console
from rich.table import Table
from rich.text import Text

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
MAX_LINE = 80
# a rail with many year marks spreads tight clusters apart, so a mark
# may legitimately sit well away from its proportional position
POSITION_SANITY = 40.0
MIN_LABELS = 2
MIN_LABEL_GAP_PERCENT = 4.0
CAPTION_SPANS = 2
AXIS_END_TOLERANCE = 0.05
AXIS_MAX_PERCENT = 100.0

# match the console style used by the other scripts in this repository
DEFAULT_CONSOLE_STYLE = "bold blue"
PASS_STYLE = "bold green"
FAIL_STYLE = "bold red"
NOTE_STYLE = "yellow"

PASS_ICON = "\uf00c"
FAIL_ICON = "\uf00d"

console = Console()

ID_RE = re.compile(r"^ID:\s*(.+)$", re.M)
TITLE_RE = re.compile(r"^title:\s*(.*?)(?=\n[a-z-]+: |\n---)", re.S | re.M)
DATE_RE = re.compile(r"^date:\s*'?(\d{4})", re.M)
CATEGORY_RE = re.compile(r"^categories:\s*(.*?)(?=\n[a-z-]+: |\n---)", re.S | re.M)
BLOCK_RE = re.compile(r"```\{=html\}\n(.*?)\n```", re.S)
FIGURE_RE = re.compile(r'<figure class="pub-timeline.*?</figure>', re.S)
MARK_RE = re.compile(
    r'<span class="pt-mark(?P<cls>[^"]*)" '
    r'style="--pt: (?P<pos>[\d.]+);">(?P<body>.*?)</span>\s*</span>',
    re.S,
)
YEAR_LABEL_RE = re.compile(r'<span class="pt-year">(\d+)</span>')
DOT_RE = re.compile(
    r'<a class="(?P<cls>pt-dot(?: pt-related)?)" href="(?P<href>[^"]*)"\n'
    r' aria-label="(?P<aria>[^"]*)"\n'
    r' title="(?P<title>[^"]*)"></a>'
)
CAPTION_RE = re.compile(r"<figcaption>(.*?)</figcaption>", re.S)
COUNT_RE = re.compile(r'<span class="pt-count">(\d+) (?:papers|presentations)</span>')
SINCE_RE = re.compile(r"since(?:\s*<span[^>]*>)?\s*(\d{4})")
TIMELINE_ICON = "fa6-solid:timeline"
CATEGORY_SPAN_RE = re.compile(
    '<span\\s+class="pt-category">([^<]*)</span>', re.S
)
LINK_RE = re.compile(r'href="([^"]*#category=[^"]*)"')
AUTHOR_RE = re.compile(r"^author:\s*(.*?)(?=\n[a-z-]+: |\n---)", re.S | re.M)

# What each area timeline is supposed to cover. "category" means every paper
# in that listing category, "authors" means the papers written with those
# co-authors, and "cited" adds the papers that the paragraph cites. Every
# area sets "cited" so that a paper the paragraph describes always has a dot,
# even when the three-tag cap keeps that paper out of the area's category.
# Only a rail that draws exactly the papers of a listing filter may link its
# caption to that filter, because a link promises exactly the set that the
# filter shows.
AREA_RULES = {
    "Flaky Tests": {"category": "flaky tests", "cited": True},
    "Database Testing": {"category": "database testing", "cited": True},
    "Web Testing": {"authors": ("Althomali", "Walsh"), "cited": True},
    "Mutation Testing": {"category": "mutation testing", "cited": True},
    "Regression Testing": {"category": "regression testing", "cited": True},
    "Search-Based Methods": {"category": "search-based methods", "cited": True},
    "Performance Evaluation": {"category": "performance analysis", "cited": True},
    "Research Methods": {"category": "research methods", "cited": True},
}


@dataclass
class Entry:
    """One paper or presentation that a timeline should draw."""

    slug: str
    identifier: str
    year: int
    title: str
    categories: set[str] = field(default_factory=set)
    authors: str = ""


@dataclass
class Figure:
    """One timeline, together with the entries it is expected to draw."""

    page: str
    label: str
    block: str
    entries: list[Entry]
    category: str | None = None
    members: list[Entry] = field(default_factory=list)
    related: list[Entry] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)
    dots: int = 0
    marks: int = 0
    labels: int = 0
    longest_line: int = 0
    positions: dict[int, float] = field(default_factory=dict)

    @property
    def years(self) -> list[int]:
        """Years that have at least one entry."""
        return sorted({entry.year for entry in self.entries})

    @property
    def expected_dots(self) -> int:
        """How many dots the timeline must contain."""
        return len(self.entries)

    @property
    def expected_members(self) -> int:
        """How many dots stand for the area's own tagged papers."""
        return len(self.members)


def yaml_scalar(raw: str) -> str:
    """Reduce a front-matter scalar to the plain text that it represents.

    A generated page quotes a title that holds an apostrophe with single
    quotes and escapes that apostrophe by doubling it, so the doubling has to
    be undone before the title is used as a label. An unquoted scalar is
    returned unchanged.
    """
    text = re.sub(r"\s+", " ", raw).strip()
    # slice rather than compare a length: a lone quote also collapses to ""
    if text[:1] == "'" and text[-1:] == "'":
        text = text[1:-1].replace("''", "'")
    return text


def load_entries(directory: pathlib.Path) -> list[Entry]:
    """Read the front matter of every entry in a directory."""
    entries = []
    for child in sorted(path for path in directory.iterdir() if path.is_dir()):
        source = child / "index.qmd"
        if not source.is_file():
            continue
        text = source.read_text(encoding="utf-8")
        identifier = ID_RE.search(text)
        date = DATE_RE.search(text)
        if not (identifier and date):
            continue
        title = TITLE_RE.search(text)
        category = CATEGORY_RE.search(text)
        author = AUTHOR_RE.search(text)
        names = set()
        if category:
            names = {item.strip() for item in category.group(1).strip("[]").split(",")}
        entries.append(
            Entry(
                slug=child.name,
                identifier=identifier.group(1).strip(),
                year=int(date.group(1)),
                title=yaml_scalar(title.group(1))
                if title
                else identifier.group(1).strip(),
                categories=names,
                authors=re.sub(r"\s+", " ", author.group(1)) if author else "",
            )
        )
    return entries


def load_category_members(directory: pathlib.Path) -> dict[str, set[str]]:
    """Map every category that the papers declare to the papers that carry it."""
    members: dict[str, set[str]] = {}
    for child in sorted(path for path in directory.iterdir() if path.is_dir()):
        source = child / "index.qmd"
        if not source.is_file():
            continue
        match = CATEGORY_RE.search(source.read_text(encoding="utf-8"))
        if not match:
            continue
        for item in match.group(1).strip("[]").split(","):
            name = item.strip()
            if name:
                members.setdefault(name, set()).add(child.name)
    return members


def relative_path(page: pathlib.Path) -> str:
    """Describe a page relative to the repository root."""
    return str(page.relative_to(REPO_ROOT))


def rule_members(rule: dict, papers: Sequence[Entry]) -> set[str]:
    """Return the slugs that a rule's category or author clause selects."""
    slugs: set[str] = set()
    if "category" in rule:
        name = rule["category"]
        slugs |= {entry.slug for entry in papers if name in entry.categories}
    if "authors" in rule:
        names = rule["authors"]
        slugs |= {
            entry.slug
            for entry in papers
            if any(name in entry.authors for name in names)
        }
    return slugs


def area_entries(
    heading: str,
    body: str,
    papers: Sequence[Entry],
    by_identifier: dict[str, Entry],
) -> list[Entry]:
    """Return the entries that the rail for one area must draw."""
    rule = AREA_RULES.get(heading)
    if not rule:
        # no rule: the caller reports this, so return a plain empty list
        return []
    members = rule_members(rule, papers)
    found: list[Entry] = [entry for entry in papers if entry.slug in members]
    if rule.get("cited"):
        keys = re.findall(r"@([A-Z][A-Za-z0-9]+)", body)
        found += [by_identifier[key] for key in keys if key in by_identifier]

    seen: set[str] = set()
    entries = []
    for entry in found:
        if entry.slug not in seen:
            seen.add(entry.slug)
            entries.append(entry)
    return entries


def page_sections(text: str) -> list[str]:
    """Split the research overview into its anchored sections."""
    parts = re.split(r'^<div id="[^"]+">[ \t]*$', text, flags=re.M)
    return [part for part in parts[1:] if "### " in part]


def area_figures(page: pathlib.Path, papers: Sequence[Entry]) -> list[Figure]:
    """Build one figure expectation per research area.

    The sections are delimited by their `<div id="...">` anchors rather than
    by a blank line before the closing `</div>`, because a paragraph may sit
    directly above that tag.
    """
    text = page.read_text(encoding="utf-8")
    by_identifier = {entry.identifier: entry for entry in papers}
    figures = []
    for part in page_sections(text):
        heading_match = re.search(r"^### (.+)$", part, re.M)
        if not heading_match:
            continue
        heading = heading_match.group(1).strip()
        blocks = BLOCK_RE.findall(part)
        block = blocks[0] if blocks else ""
        entries = area_entries(heading, part, papers, by_identifier)
        rule = AREA_RULES.get(heading, {})
        own = rule_members(rule, papers) if rule else {e.slug for e in entries}
        members = [entry for entry in entries if entry.slug in own]
        related = [entry for entry in entries if entry.slug not in own]
        link = LINK_RE.search(block)
        figure = (
            Figure(
                page=relative_path(page),
                label=heading,
                block=block,
                entries=entries,
                category=link.group(1) if link else None,
                members=members,
                related=related,
            )
        )
        if heading not in AREA_RULES:
            figure.problems.append(
                f"{heading} has no membership rule in AREA_RULES"
            )
        figures.append(figure)
    return figures


def page_figure(page: pathlib.Path, entries: Sequence[Entry]) -> Figure:
    """Build the expectation for the timeline of a whole page."""
    blocks = BLOCK_RE.findall(page.read_text(encoding="utf-8"))
    return Figure(
        page=relative_path(page),
        label="all entries",
        block=blocks[-1] if blocks else "",
        entries=list(entries),
        members=list(entries),
    )


def check_structure(figure: Figure) -> None:
    """Check the parts of a timeline that are always required."""
    if not figure.block:
        figure.problems.append("no ```{=html} timeline block was found")
        return
    if 'class="pub-timeline' not in figure.block:
        figure.problems.append("the block has no .pub-timeline figure")
    if "<figcaption>" not in figure.block:
        figure.problems.append("the figure has no figcaption")
    if figure.block.count('<span class="pt-line"') != 1:
        figure.problems.append("the axis must be drawn exactly once")
    if "<pre>" in figure.block or "<code>" in figure.block:
        figure.problems.append("nested HTML became a code block (pandoc indentation)")
    lines = figure.block.splitlines()
    if lines:
        figure.longest_line = max(len(line) for line in lines)
    for number, line in enumerate(lines, start=1):
        if len(line) > MAX_LINE:
            figure.problems.append(
                f"line {number} is {len(line)} columns, over {MAX_LINE}"
            )


def check_caption(figure: Figure) -> None:
    """Check the caption against the expected entries."""
    caption = CAPTION_RE.search(figure.block)
    if not caption or not figure.entries:
        return
    text = caption.group(1)
    count = COUNT_RE.search(text)
    if not count:
        figure.problems.append("the caption does not state how many entries")
    elif int(count.group(1)) != figure.expected_members:
        figure.problems.append(
            f"the caption says {count.group(1)} entries,"
            f" not {figure.expected_members}"
        )
    icons = re.findall(r'<iconify-icon[^>]*icon="([^"]+)"', caption.group(0))
    if icons != [TIMELINE_ICON]:
        figure.problems.append(
            f"the caption icons are {icons}, expected only {TIMELINE_ICON}"
        )
    icon_at = caption.group(0).find("<iconify-icon")
    link_at = caption.group(0).find("<a href=")
    if link_at != -1 and icon_at > link_at:
        figure.problems.append(
            "the timeline icon sits inside the caption link; it must come"
            " before the link so that it is not clickable"
        )
    spans = CATEGORY_SPAN_RE.findall(text)
    if len(spans) != CAPTION_SPANS:
        figure.problems.append(
            f"the caption has {len(spans)} pt-category spans, not {CAPTION_SPANS}"
        )
    elif not spans[0].strip():
        figure.problems.append("the caption does not name the area")
    first = min(entry.year for entry in (figure.members or figure.entries))
    since = SINCE_RE.search(text)
    if not since:
        figure.problems.append("the caption does not name the first year")
    elif int(since.group(1)) != first:
        figure.problems.append(f"the caption says since {since.group(1)}, not {first}")


def check_marks(figure: Figure) -> None:
    """Check the year marks, their positions, and their dots."""
    marks = list(MARK_RE.finditer(figure.block))
    figure.marks = len(marks)
    years = figure.years
    if len(marks) != len(years):
        figure.problems.append(
            f"{len(marks)} year marks for {len(years)} years with entries"
        )
        return
    span = max(1, years[-1] - years[0])
    for year, mark in zip(years, marks):
        position = float(mark.group("pos"))
        figure.positions[year] = position
        if not 0.0 <= position <= AXIS_MAX_PERCENT:
            figure.problems.append(f"{year} sits at {position}%, outside the axis")
        # tight clusters are deliberately pushed apart, so the position
        # only has to stay within POSITION_SANITY of the proportional one
        proportional = (year - years[0]) / span * 100
        if abs(position - proportional) > POSITION_SANITY:
            figure.problems.append(
                f"{year} sits at {position}%,"
                f" far from its proportional {proportional:.1f}%"
            )
        member_wanted = sum(1 for entry in figure.members if entry.year == year)
        related_wanted = sum(1 for entry in figure.related if entry.year == year)
        found = list(DOT_RE.finditer(mark.group("body")))
        member_found = sum(1 for dot in found if dot.group("cls") == "pt-dot")
        related_found = len(found) - member_found
        if (member_found, related_found) != (member_wanted, related_wanted):
            figure.problems.append(
                f"{year} draws {member_found} area dots and {related_found}"
                f" related dots, not {member_wanted} and {related_wanted}"
            )
    check_axis(figure, years)


def check_axis(figure: Figure, years: Sequence[int]) -> None:
    """Check that the axis starts at the first year and ends at the last."""
    if not years:
        return
    first = figure.positions.get(years[0], 0.0)
    last = figure.positions.get(years[-1], 100.0)
    if abs(first) > AXIS_END_TOLERANCE:
        figure.problems.append(f"the axis starts at {first}%, not 0%")
    if abs(last - 100.0) > AXIS_END_TOLERANCE:
        figure.problems.append(f"the axis ends at {last}%, not 100%")
    ordered = [figure.positions.get(year, 0.0) for year in years]
    if any(before >= after for before, after in itertools.pairwise(ordered)):
        figure.problems.append("the marks do not advance with the years")


def check_labels(figure: Figure) -> None:
    """Check the year labels on the axis."""
    labels = [int(value) for value in YEAR_LABEL_RE.findall(figure.block)]
    figure.labels = len(labels)
    years = figure.years
    if not years:
        return
    if len(labels) < MIN_LABELS:
        figure.problems.append(
            f"the axis has {len(labels)} labels, fewer than {MIN_LABELS}"
        )
    if len(set(labels)) != len(labels):
        figure.problems.append("the axis labels a year more than once")
    for year in labels:
        if year not in years:
            figure.problems.append(f"the axis labels {year}, which has no entry")
    if years[0] not in labels:
        figure.problems.append("the axis does not label the first year")
    if years[-1] not in labels:
        figure.problems.append("the axis does not label the last year")
    ordered = sorted(labels)
    for before, after in itertools.pairwise(ordered):
        gap = figure.positions.get(after, 0) - figure.positions.get(before, 0)
        if gap < MIN_LABEL_GAP_PERCENT:
            figure.problems.append(
                f"the labels {before} and {after} sit {gap:.1f}% apart"
            )


def check_dots(figure: Figure) -> None:
    """Check that every dot points at one expected entry."""
    dots = list(DOT_RE.finditer(figure.block))
    bare = len(re.findall(r'<a class="pt-dot(?: pt-related)?"', figure.block))
    figure.dots = len(dots)
    if len(dots) != bare:
        figure.problems.append(f"{bare} dots, but only {len(dots)} carry a title")
    expected = {entry.slug for entry in figure.entries}
    seen = {}
    for dot in dots:
        href = dot.group("href")
        slug = pathlib.PurePosixPath(href).name
        seen[slug] = href
        if slug not in expected:
            figure.problems.append(f"{slug} is not an entry of this timeline")
        year = dot.group("title").split(" &middot; ")[0]
        entry_year = [e.year for e in figure.entries if e.slug == slug]
        if not year.isdigit() or (entry_year and int(year) != entry_year[0]):
            figure.problems.append(f"{slug} does not carry its own year")
    missing = expected - set(seen)
    if missing:
        shown = ", ".join(sorted(missing)[:4])
        figure.problems.append(f"{len(missing)} entries have no dot: {shown}")


def resolve_link(page: str, href: str) -> pathlib.Path:
    """Resolve a link in a page, which may be absolute or relative."""
    path = href.partition("#")[0]
    if path.startswith("/"):
        return (REPO_ROOT / path.lstrip("/")).resolve()
    return ((REPO_ROOT / page).parent / path).resolve()


def check_targets(figure: Figure) -> None:
    """Check that every dot link resolves to a real entry directory."""
    for match in DOT_RE.finditer(figure.block):
        href = match.group("href").partition("#")[0]
        target = resolve_link(figure.page, href)
        if not (target / "index.qmd").is_file():
            figure.problems.append(f"{href} does not hold an index.qmd")


def check_category(figure: Figure, members: dict[str, set[str]]) -> None:
    """Check that a linked caption names a filter that the rail matches.

    A caption may only link a listing filter when the rail draws exactly the
    papers in that filter; otherwise the caption count and the filtered
    listing would disagree.
    """
    if not figure.category:
        return
    name = figure.category.partition("#category=")[2].replace("%20", " ")
    if name not in members:
        figure.problems.append(f"the caption links to unknown category {name}")
        return
    in_filter = members[name]
    own = {entry.slug for entry in figure.members}
    if own != in_filter:
        figure.problems.append(
            f"the caption links a filter with {len(in_filter)} papers,"
            f" but the area draws {len(own)}"
        )


def site_html(target: pathlib.Path) -> pathlib.Path:
    """Return the built page for a source directory."""
    if target.is_dir():
        return target / "index.html"
    return target


def check_site(figures: Sequence[Figure], site: pathlib.Path) -> list[str]:
    """Check the rendered HTML of the pages that carry a timeline."""
    problems = []
    pages = sorted({figure.page for figure in figures})
    for page in pages:
        html = site / page.replace(".qmd", ".html")
        if not html.is_file():
            problems.append(f"{html} was not built")
            continue
        text = html.read_text(encoding="utf-8")
        wanted = sum(figure.expected_dots for figure in figures if figure.page == page)
        found = len(re.findall(r'class="pt-dot(?: pt-related)?"', text))
        if found != wanted:
            problems.append(f"{page}: {found} dots in the built page, not {wanted}")
        problems += check_built_figures(page, text)
    return problems


def check_built_figures(page: str, text: str) -> list[str]:
    """Check that the dots inside the built figures have built targets."""
    problems = []
    for figure in FIGURE_RE.findall(text):
        if "<pre>" in figure or "<code>" in figure:
            problems.append(f"{page}: a rendered figure holds a code block")
        for href in set(
            re.findall(r'class="pt-dot(?: pt-related)?" href="([^"]*)"', figure)
        ):
            target = resolve_link(page, href)
            built = site_html(target)
            if not built.is_file():
                problems.append(f"{page}: {href} has no built page")
    return problems


def show(figures: Sequence[Figure]) -> None:
    """Render every timeline as a row, grouped by page."""
    for page in sorted({figure.page for figure in figures}):
        table = Table(
            title=page,
            title_style=DEFAULT_CONSOLE_STYLE,
            title_justify="left",
            header_style=DEFAULT_CONSOLE_STYLE,
            box=None,
        )
        table.add_column("Timeline", no_wrap=True)
        table.add_column("Entries", justify="right")
        table.add_column("Dots", justify="right")
        table.add_column("Related", justify="right")
        table.add_column("Years", justify="right")
        table.add_column("Labels", justify="right")
        table.add_column("Width", justify="right")
        table.add_column("Result", no_wrap=True)
        for figure in figures:
            if figure.page != page:
                continue
            result = Text(f"{FAIL_ICON} fail", style=FAIL_STYLE)
            if not figure.problems:
                result = Text(f"{PASS_ICON} pass", style=PASS_STYLE)
            table.add_row(
                Text(figure.label),
                str(figure.expected_dots),
                str(figure.dots),
                str(len(figure.related)),
                str(figure.marks),
                str(figure.labels),
                str(figure.longest_line),
                result,
            )
        console.print(table)


def report(figures: Sequence[Figure], problems: Sequence[str]) -> bool:
    """Show the problems of every figure and return whether all passed."""
    failed = [figure for figure in figures if figure.problems]
    for figure in failed:
        console.print(f"{FAIL_ICON} {figure.page}: {figure.label}", style=FAIL_STYLE)
        for problem in figure.problems:
            console.print(Text(f"     - {problem}", style="red"))
    if problems:
        console.print(f"{FAIL_ICON} BUILD: ISSUES ({len(problems)})", style=FAIL_STYLE)
        for problem in problems:
            console.print(Text(f"     - {problem}", style="red"))
    if not failed and not problems:
        console.print(
            f"{PASS_ICON} TIMELINES: PASS ({len(figures)} timelines, no issues)",
            style=PASS_STYLE,
        )
        return True
    console.print(
        f"{FAIL_ICON} TIMELINES: ISSUES ({len(failed)} of {len(figures)} timelines)",
        style=FAIL_STYLE,
    )
    return False


def build_parser() -> argparse.ArgumentParser:
    """Describe the command line interface of the tool."""
    parser = argparse.ArgumentParser(
        description="Verify the timelines on the research pages.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "The tool exits with 0 when every timeline matches the front\n"
            "matter of the papers and presentations that it draws."
        ),
    )
    parser.add_argument(
        "--target",
        choices=["all", "areas", "papers", "presentations"],
        default="all",
        help="which timeline to verify (default: all)",
    )
    parser.add_argument(
        "--site",
        type=pathlib.Path,
        default=None,
        help="also check a rendered build, for example --site _site",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="print only the summary and the problems",
    )
    return parser


def collect(target: str) -> list[Figure]:
    """Build the expected figures for the requested target."""
    papers_dir = REPO_ROOT / "research" / "papers"
    talks_dir = REPO_ROOT / "research" / "presentations"
    papers = load_entries(papers_dir)
    figures: list[Figure] = []
    if target in ("all", "areas"):
        page = REPO_ROOT / "research" / "index.qmd"
        figures += area_figures(page, papers)
    if target in ("all", "papers"):
        figures.append(page_figure(papers_dir / "index.qmd", papers))
    if target in ("all", "presentations"):
        figures.append(page_figure(talks_dir / "index.qmd", load_entries(talks_dir)))
    return figures


def main(argv: Sequence[str] | None = None) -> int:
    """Verify the timelines and report the result."""
    args = build_parser().parse_args(argv)
    papers_dir = REPO_ROOT / "research" / "papers"
    figures = collect(args.target)
    members = load_category_members(papers_dir)

    for figure in figures:
        check_structure(figure)
        if not figure.block:
            continue
        check_caption(figure)
        check_marks(figure)
        check_labels(figure)
        check_dots(figure)
        check_targets(figure)
        check_category(figure, members)

    problems = []
    if args.site:
        problems = check_site(figures, args.site.resolve())

    if not args.quiet:
        show(figures)
    ok = report(figures, problems)
    if args.site:
        console.print(
            Text(f"     rendered build checked under {args.site}"),
            style=NOTE_STYLE,
        )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
