"""Fetch the transcript and the details of a Software Engineering Radio episode.

Given the URL of an episode page, this tool downloads the automatically
generated transcript that Software Engineering Radio publishes, saves it to
a cache outside of the repository, and reports the details that a blog post
needs: the episode number and title, the number of speaker turns in the
transcript, and the URL of the episode's MP3 file together with a ready to
paste Quarto audio shortcode.

The tool is useful before a blog post exists. Fetch a transcript as soon as
an episode is published, read or search it, and then hand the cached file to
_tools/verify-seradio-post.py once the post is written. Run the tool with
uv run so that the rich dependency declared in pyproject.toml is available:

    uv run _tools/fetch-seradio-transcript.py --url <episode-page-url>

Examples
--------
Fetch a transcript, save it in the cache, and show the episode details:

    uv run _tools/fetch-seradio-transcript.py \
        --url <episode-page-url>

Print a transcript so that it can be read or searched. The report goes to
standard error, which keeps the piped transcript free of any extra text:

    uv run _tools/fetch-seradio-transcript.py \
        --url <episode-page-url> --stdout | grep -i mutation

Write a transcript to a specific file, replacing an existing copy:

    uv run _tools/fetch-seradio-transcript.py \
        --url <episode-page-url> --output /tmp/726-transcript.txt --force

List every transcript that is already in the cache:

    uv run _tools/fetch-seradio-transcript.py --list

Transcripts are cached outside of the repository in
~/.cache/seradio-transcripts so that the published text of an episode is
never committed. See README.md for how this tool and
_tools/verify-seradio-post.py fit into the writing process.
"""

from __future__ import annotations

import argparse
import html
import importlib
import pathlib
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from typing import Sequence

from rich.console import Console
from rich.table import Table
from rich.text import Text

CACHE_DIR = pathlib.Path.home() / ".cache" / "seradio-transcripts"
URL_TIMEOUT = 30

# match the console style used by the other scripts in this repository
DEFAULT_CONSOLE_STYLE = "bold blue"
NOTE_STYLE = "yellow"
PASS_ICON = "\uf00c"
FAIL_ICON = "\uf00d"

# the report is written to standard error so that a transcript written to
# standard output can always be piped on its own; run the tool without
# --stdout to send the transcript to a file and read the report as usual
console = Console(stderr=True)

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# the markers that end the transcript content on an episode page
END_MARKERS = ("</article>", "<footer", "megaphone-footer", 'id="comments"')

# text that follows the transcript when a page is not trimmed correctly
FOOTER_TEXT = ("What People Are Saying", "Recent posts", "Advertise")

# a speaker turn looks like "Gregory Kapfhammer 00:00:18 Welcome ..."
TURN_RE = re.compile(
    r"^\D{2,40}?\s+\d{1,2}[:'\u2032\u2019]\d{2}[:'\u2032\u2019]\d{2}\s+",
    re.M,
)

TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
EMBED_RE = re.compile(r"embed/episode/id/(\d+)")
MP3_RE = re.compile(r"https?://traffic\.libsyn\.com/[^\"'\s\\]*?\.mp3")
EPISODE_RE = re.compile(r"se-radio-(\d+)-")


def tls_context() -> ssl.SSLContext:
    """Build a TLS context that also works under the uv interpreter.

    The interpreter in .venv does not always locate a system CA bundle
    (for example on NixOS, where /etc/ssl/cert.pem is absent), which makes
    every HTTPS request fail with CERTIFICATE_VERIFY_FAILED. The certifi
    bundle, which the environment already provides, is used when the
    package can be imported, falling back to the default context when it
    cannot.
    """
    try:
        certifi = importlib.import_module("certifi")
    except ModuleNotFoundError:
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=certifi.where())


def fetch(url: str, method: str = "GET") -> str:
    """Download a page and return its text."""
    request = urllib.request.Request(
        url,
        method=method,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(
            request, timeout=URL_TIMEOUT, context=tls_context()
        ) as reply:
            return reply.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as error:
        raise SystemExit(f"could not download {url} -> HTTP {error.code}")
    except (urllib.error.URLError, OSError) as error:
        raise SystemExit(f"could not download {url} -> {error}")


def extract_transcript(page: str) -> str:
    """Return the transcript text of an episode page, without the footer."""
    marker = page.lower().find("transcript brought to you")
    if marker < 0:
        raise SystemExit("this page does not contain a transcript")
    section = page[marker:]
    # the transcript ends where the article, the comments, or the footer
    # of the page starts, so cut the markup at the earliest such marker
    end = len(section)
    for pattern in END_MARKERS:
        hit = section.lower().find(pattern.lower())
        if hit != -1:
            end = min(end, hit)
    section = section[:end]
    section = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", section, flags=re.S)
    section = re.sub(r"<br\s*/?>|</p>|</div>", "\n", section)
    section = re.sub(r"<[^>]+>", "", section)
    section = html.unescape(section)
    section = re.sub(r"[ \t]+", " ", section)
    section = re.sub(r"\n\s*\n+", "\n", section).strip()
    # safety net in case the page markup changes and some site navigation
    # text survives the cut at the end of the transcript content
    for junk in FOOTER_TEXT:
        cut = section.find(junk)
        if cut != -1:
            section = section[:cut].rstrip()
    return section


def derive_episode(url: str, page: str, title: str) -> str:
    """Work out the episode number from the URL, the page, or the title."""
    for source in (url, title, page):
        match = EPISODE_RE.search(source) or re.search(r"SE Radio (\d+):", source, re.I)
        if match:
            return match.group(1)
    return "episode"


def derive_title(page: str) -> str:
    """Return the episode title from the title element of a page."""
    match = TITLE_RE.search(page)
    if not match:
        return "unknown title"
    title = html.unescape(re.sub(r"\s+", " ", match.group(1))).strip()
    for suffix in ("\u2013", "-", "\u2014"):
        head, separator, _ = title.rpartition(f" {suffix} ")
        if separator and "SE Radio" in head:
            return head.strip()
    return title


def find_mp3(page: str) -> str | None:
    """Find the MP3 file of an episode by reading its player embed."""
    embed = EMBED_RE.search(page)
    if not embed:
        return None
    embed_url = (
        "https://html5-player.libsyn.com/embed/episode/id/"
        f"{embed.group(1)}/height/128/theme/modern/size/standard"
    )
    embed_page = fetch(embed_url).replace("\\/", "/")
    candidates = sorted(set(MP3_RE.findall(embed_page)))
    preferred = [u for u in candidates if "/forcedn/" in u]
    chosen = (preferred or candidates or [""])[0]
    if chosen and "/forcedn/" in chosen and "/secure/" not in chosen:
        chosen = chosen.replace("traffic.libsyn.com/", "traffic.libsyn.com/secure/", 1)
    # the episode pages hand out http links, while the posts use https
    return chosen.replace("http://", "https://", 1) or None


def check_mp3(url: str) -> str:
    """Return a short description of the HTTP status of an MP3 link."""
    request = urllib.request.Request(
        url, method="HEAD", headers={"User-Agent": USER_AGENT}
    )
    try:
        with urllib.request.urlopen(
            request, timeout=URL_TIMEOUT, context=tls_context()
        ) as reply:
            content_type = reply.headers.get("Content-Type", "")
            return f"{reply.status} {content_type}".strip()
    except urllib.error.HTTPError as error:
        return f"HTTP {error.code}"
    except (urllib.error.URLError, OSError) as error:
        return f"unverified ({error})"


def summarize(transcript: str) -> tuple[int, int, int]:
    """Return the number of turns, words, and characters in a transcript."""
    turns = len(TURN_RE.findall(transcript))
    words = len(transcript.split())
    return turns, words, len(transcript)


def audio_shortcode(mp3: str, episode: str) -> str:
    """Return the Quarto shortcode that embeds the episode audio."""
    caption = f"Listen to Software Engineering Radio Episode {episode}"
    return f'{{{{< audio\nfile="{mp3}"\ncaption="{caption}" >}}}}'


def show_summary(fields: Sequence[tuple[str, str]]) -> None:
    """Render the details of an episode as a table."""
    table = Table(
        title="episode details",
        title_style=DEFAULT_CONSOLE_STYLE,
        header_style=DEFAULT_CONSOLE_STYLE,
        show_header=False,
    )
    table.add_column("Field", style=DEFAULT_CONSOLE_STYLE, no_wrap=True)
    table.add_column("Value")
    for field, value in fields:
        table.add_row(Text(field), Text(value))
    console.print(table)


def show_cached(cache: pathlib.Path) -> None:
    """Render the transcripts that are already in the cache."""
    files = sorted(cache.glob("*-transcript.txt"))
    if not files:
        console.print(f"no transcripts cached in {cache}", style=NOTE_STYLE)
        return
    table = Table(
        title=f"{len(files)} cached transcripts in {cache}",
        title_style=DEFAULT_CONSOLE_STYLE,
        header_style=DEFAULT_CONSOLE_STYLE,
    )
    table.add_column("Episode", no_wrap=True)
    table.add_column("Turns", justify="right", no_wrap=True)
    table.add_column("Words", justify="right", no_wrap=True)
    table.add_column("Size", justify="right", no_wrap=True)
    table.add_column("Modified", no_wrap=True)
    for path in files:
        transcript = path.read_text(encoding="utf-8", errors="replace")
        turns, words, _ = summarize(transcript)
        modified = time.strftime("%Y-%m-%d", time.localtime(path.stat().st_mtime))
        table.add_row(
            Text(path.stem.replace("-transcript", "")),
            str(turns),
            f"{words:,}",
            f"{path.stat().st_size:,}",
            modified,
        )
    console.print(table)


def build_parser() -> argparse.ArgumentParser:
    """Create the command line interface for the tool."""
    parser = argparse.ArgumentParser(
        description=(
            "Fetch the transcript and the details of a Software "
            "Engineering Radio episode."
        )
    )
    parser.add_argument(
        "--url",
        help="URL of the Software Engineering Radio episode page",
    )
    parser.add_argument(
        "--episode",
        help="episode number, used to name the cached transcript",
    )
    parser.add_argument(
        "--cache",
        type=pathlib.Path,
        default=CACHE_DIR,
        help=f"cache directory (default: {CACHE_DIR})",
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        help="write the transcript to this path instead of the cache",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="write the transcript to standard output only",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="download the transcript even when it is already cached",
    )
    parser.add_argument(
        "--no-mp3",
        action="store_true",
        help="do not look up the MP3 file of the episode",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="list the transcripts in the cache and exit",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Fetch a transcript and report the details of an episode."""
    args = build_parser().parse_args(argv)

    if args.list:
        show_cached(args.cache)
        return 0

    if not args.url:
        console.print(
            f"{FAIL_ICON} provide --url, or use --list to show the cache",
            style="bold red",
        )
        return 1

    page = fetch(args.url)
    transcript = extract_transcript(page)
    title = derive_title(page)
    episode = args.episode or derive_episode(args.url, page, title)

    if args.stdout:
        sys.stdout.write(f"{transcript}\n")
        destination = "standard output"
    else:
        path = args.output or args.cache / f"{episode}-transcript.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.is_file() and not args.force:
            destination = f"{path} (already cached, use --force to refresh)"
            transcript = path.read_text(encoding="utf-8", errors="replace")
        else:
            path.write_text(f"{transcript}\n", encoding="utf-8")
            destination = str(path)

    turns, words, characters = summarize(transcript)
    fields = [
        ("Episode", str(episode)),
        ("Title", title),
        ("Transcript", destination),
        ("Speaker turns", str(turns)),
        ("Words", f"{words:,}"),
        ("Characters", f"{characters:,}"),
    ]

    mp3 = None if args.no_mp3 else find_mp3(page)
    if mp3:
        fields.append(("MP3 file", mp3))
        fields.append(("MP3 status", check_mp3(mp3)))

    console.print()
    show_summary(fields)

    if mp3:
        console.print()
        console.print("audio shortcode:", style=DEFAULT_CONSOLE_STYLE)
        for line in audio_shortcode(mp3, str(episode)).splitlines():
            # soft_wrap keeps the shortcode on one line when it is copied
            console.print(Text(f"    {line}"), soft_wrap=True)

    console.print()
    console.print(
        f"{PASS_ICON} fetched the transcript of episode {episode}",
        style="bold green",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
