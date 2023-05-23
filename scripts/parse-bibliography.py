"""Parse the bibtex file."""

import sys
from pathlib import Path

import bibtexparser
import yaml
from rich.console import Console

if __name__ == "__main__":
    print(f"Arguments count: {len(sys.argv)}")
    for i, argument in enumerate(sys.argv):
        print(f"Argument {i:>6}: {argument}")

    bibliography = None
    if len(sys.argv) == 1:
        bib_database_file_name = "bibliography/bibtex/bibliography_kapfhammer.bib"
    else:
        bib_database_file_name = sys.argv[1]

    with open(bib_database_file_name, encoding="utf-8") as bibtex_file:
        bibliography = bibtexparser.load(bibtex_file)

    console = Console()
    console.print(
        f":rocket: Always run from root to parsing the {bib_database_file_name}"
    )
    console.print(len(bibliography.entries))

    for publication in bibliography.entries:
        console.print(publication)
        console.print(".")
        publication_id = publication["ID"]
        publication_year = publication["year"]
        publication_abstract = publication["abstract"]
        publication_booktitle = publication["booktitle"]
        publication["description"] = f"<em>{publication_booktitle}</em>"
        publication_abstract = publication_abstract.replace("\n", " ")
        publication["abstract"] = publication_abstract
        console.print(publication_id)
        papers_directory = Path(f"papers/{publication_year}-{publication_id}/")
        papers_directory.mkdir(parents=True, exist_ok=True)
        publication_file = Path(papers_directory / "index.qmd")
        publication_file.touch()
        publication_file.write_text(
            f"---\n{yaml.dump(publication, allow_unicode=True, default_flow_style=False)}\n---",
            encoding="utf-8",
        )
