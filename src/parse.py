"""Parse the bibtex file."""

import sys
from pathlib import Path

import bibtexparser
import yaml
from rich.console import Console

if __name__ == "__main__":
    # Main function for the parse script.
    print(f"Arguments count: {len(sys.argv)}")
    for i, argument in enumerate(sys.argv):
        print(f"Argument {i:>6}: {argument}")

    bibliography = None
    bib_database_file_name = sys.argv[1]
    with open(bib_database_file_name, encoding="utf-8") as bibtex_file:
        bibliography = bibtexparser.load(bibtex_file)

    console = Console()
    console.print(
        f":rocket: Always run from root to parsing the {bib_database_file_name}"
    )
    # console.print(bibliography.entries)

    for publication in bibliography.entries:
        console.print(publication)
        publication_id = publication["ID"]
        publication_year = publication["year"]
        console.print(publication_id)
        papers_directory = Path(f"papers/{publication_year}-{publication_id}/")
        papers_directory.mkdir(parents=True, exist_ok=True)
        publication_file_name = Path(papers_directory / "index.qmd")
        publication_file_name.touch()
        publication_file_name.write_text(
            yaml.dump(publication, allow_unicode=True, default_flow_style=False),
            encoding="utf-8",
        )
