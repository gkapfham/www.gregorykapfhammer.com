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
POSITION_SANITY = 25.0
MIN_LABELS = 2
MIN_LABEL_GAP_PERCENT = 4.0
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
    r'<a class="pt-dot" href="(?P<href>[^"]*)"\n'
    r' aria-label="(?P<aria>[^"]*)"\n'
    r' title="(?P<title>[^"]*)"></a>'
)
CAPTION_RE = re.compile(r"<figcaption>(.*?)</figcaption>", re.S)
COUNT_RE = re.compile(r'<span class="pt-count">(\d+) (?:papers|presentations)</span>')
SINCE_RE = re.compile(r"(?:since|&middot;)\s*(\d{4})")
LINK_RE = re.compile(r'href="([^"]*#category=[^"]*)"')
AUTHOR_RE = re.compile(r"^author:\s*(.*?)(?=\n[a-z-]+: |\n---)", re.S | re.M)

# What each area timeline is supposed to cover. "category" means every paper
# in that listing category, "authors" means the papers written with those
# co-authors, and "cited" adds the papers that the paragraph cites. Only a
# rule that is a bare category may link its caption to the listing filter,
# because a link promises exactly the set that the filter shows.
AREA_RULES = {
    "Flaky Tests": {"category": "flaky tests"},
    "Database Testing": {"category": "database testing"},
    "Web Testing": {"authors": ("Althomali", "Walsh")},
    "Mutation Testing": {"category": "mutation testing"},
    "Regression Testing": {"category": "regression testing"},
    "Search-Based Testing": {"category": "search-based methods"},
    "Performance Evaluation": {"category": "performance analysis"},
    "Research Methods": {"category": "human study", "cited": True},
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
    link_allowed: bool = False
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
                title=re.sub(r"\s+", " ", title.group(1)).strip().strip("'")
                if title
                else identifier.group(1).strip(),
                categories=names,
                authors=re.sub(r"\s+", " ", author.group(1)) if author else "",
            )
        )
    return entries


def load_categories(directory: pathlib.Path) -> set[str]:
    """Collect every category that the papers declare."""
    categories = set()
    for child in sorted(path for path in directory.iterdir() if path.is_dir()):
        source = child / "index.qmd"
        if not source.is_file():
            continue
        match = CATEGORY_RE.search(source.read_text(encoding="utf-8"))
        if match:
            for item in match.group(1).strip("[]").split(","):
                categories.add(item.strip())
    return categories


def relative_path(page: pathlib.Path) -> str:
    """Describe a page relative to the repository root."""
    return str(page.relative_to(REPO_ROOT))


def area_entries(
    heading: str,
    body: str,
    papers: Sequence[Entry],
    by_identifier: dict[str, Entry],
) -> tuple[list[Entry], str | None]:
    """Return the entries and the category that the rail may link to."""
    rule = AREA_RULES.get(heading)
    if not rule:
        return [], None
    found: list[Entry] = []
    if "category" in rule:
        name = rule["category"]
        found += [entry for entry in papers if name in entry.categories]
    if "authors" in rule:
        names = rule["authors"]
        found += [
            entry for entry in papers if any(name in entry.authors for name in names)
        ]
    if rule.get("cited"):
        keys = re.findall(r"@([A-Z][A-Za-z0-9]+)", body)
        found += [by_identifier[key] for key in keys if key in by_identifier]

    seen: set[str] = set()
    entries = []
    for entry in found:
        if entry.slug not in seen:
            seen.add(entry.slug)
            entries.append(entry)
    pure = set(rule) == {"category"}
    return entries, rule["category"] if pure else None


def area_figures(page: pathlib.Path, papers: Sequence[Entry]) -> list[Figure]:
    """Build one figure expectation per research area."""
    text = page.read_text(encoding="utf-8")
    by_identifier = {entry.identifier: entry for entry in papers}
    figures = []
    pattern = r"### ([^\n]+)\n\n(.*?)(?=\n\n</div>)"
    for match in re.finditer(pattern, text, re.S):
        heading, body = match.group(1), match.group(2)
        blocks = BLOCK_RE.findall(body)
        block = blocks[0] if blocks else ""
        entries, allowed = area_entries(heading, body, papers, by_identifier)
        link = LINK_RE.search(block)
        figures.append(
            Figure(
                page=relative_path(page),
                label=heading,
                block=block,
                entries=entries,
                category=link.group(1) if link else None,
                link_allowed=allowed is not None,
            )
        )
    return figures


def page_figure(page: pathlib.Path, entries: Sequence[Entry]) -> Figure:
    """Build the expectation for the timeline of a whole page."""
    blocks = BLOCK_RE.findall(page.read_text(encoding="utf-8"))
    return Figure(
        page=relative_path(page),
        label="all entries",
        block=blocks[-1] if blocks else "",
        entries=list(entries),
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
    elif int(count.group(1)) != figure.expected_dots:
        figure.problems.append(
            f"the caption says {count.group(1)} entries, not {figure.expected_dots}"
        )
    first = min(entry.year for entry in figure.entries)
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
        wanted = sum(1 for entry in figure.entries if entry.year == year)
        if len(DOT_RE.findall(mark.group("body"))) != wanted:
            figure.problems.append(
                f"{year} draws "
                f"{len(DOT_RE.findall(mark.group('body')))} dots"
                f" for {wanted} entries"
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
    bare = len(re.findall(r'<a class="pt-dot"', figure.block))
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


def check_category(figure: Figure, categories: set[str]) -> None:
    """Check that a linked caption names a category that exists."""
    if not figure.category:
        return
    raw = figure.category.split("#category=")[-1]
    name = raw.replace("%20", " ")
    if name not in categories:
        figure.problems.append(f"the caption links to unknown category {name}")
    if not figure.link_allowed:
        figure.problems.append(
            "the caption links a listing filter, but the rail covers"
            " more than that filter, so the count and the link disagree"
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
        found = len(re.findall(r'class="pt-dot"', text))
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
        for href in set(re.findall(r'class="pt-dot" href="([^"]*)"', figure)):
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
    categories = load_categories(papers_dir)

    for figure in figures:
        check_structure(figure)
        if not figure.block:
            continue
        check_caption(figure)
        check_marks(figure)
        check_labels(figure)
        check_dots(figure)
        check_targets(figure)
        check_category(figure, categories)

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
