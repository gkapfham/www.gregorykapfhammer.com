"""Parse the bibtex file."""

import bibtexparser

from rich.console import Console

import sys

if __name__ == "__main__":
    # Main function for the parse script.
    print(f"Arguments count: {len(sys.argv)}")
    for i, argument in enumerate(sys.argv):
        print(f"Argument {i:>6}: {argument}")

    bib_database = ""
    with open(sys.argv[1], encoding="utf-8") as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)

    console = Console()
    console.print(
        f":rocket: Hi! I'm a researcher, Teacher, and Software Developer!"
    )
    console.print(bib_database.entries)
