"""Parse the bibtex file."""

import sys
import shutil
from pathlib import Path

import bibtexparser
import yaml
from rich.console import Console

from typing import Dict

console = Console()


def parse_conference_paper(publication: Dict[str, str]):
    """Parse a conference paper, noted because it uses a booktitle."""
    if publication.get("booktitle"):
        print("Found something!")
        # extract values from the current publication
        publication_id = publication["ID"]
        publication_year = publication["year"]
        publication_abstract = publication["abstract"]
        publication_booktitle = publication["booktitle"]
        console.print(publication_id)
        # define the description using the booktitle
        publication["description"] = f"<em>{publication_booktitle}</em>"
        # redefine the abstract so that there are no newlines in it
        publication_abstract = publication_abstract.replace("\n", " ")
        publication["abstract"] = publication_abstract
        # define the date so that it is a string in YYYY-MM-DD format;
        # note that this sets up the date so that the MM and the DD
        # will be ignored later as conference papers do not need MM or DD
        publication_year = publication["year"]
        del publication["year"]
        publication["date"] = f"{publication_year}-01-01"
        # define the date-format to only display the year
        only_year = "YYYY"
        publication["date-format"] = f"{only_year}"
        # create the file in the papers directory
        papers_directory = Path(f"papers/{publication_year}-{publication_id}/")
        papers_directory.mkdir(parents=True, exist_ok=True)
        publication_file = Path(papers_directory / "index.qmd")
        publication_file.touch()
        publication_file.write_text(
            f"---\n{yaml.dump(publication, allow_unicode=True, default_flow_style=False)}\n---",
            encoding="utf-8",
        )


if __name__ == "__main__":
    # display the command-line arguments
    print(f"Arguments count: {len(sys.argv)}")
    for i, argument in enumerate(sys.argv):
        print(f"Argument {i:>6}: {argument}")
    # determine whether to use the default bibliography
    # (if one is not specified) or to use a specified
    # one, normally provided for testing purposes
    bibliography = None
    if len(sys.argv) == 1:
        bib_database_file_name = "bibliography/bibtex/bibliography_kapfhammer.bib"
    else:
        bib_database_file_name = sys.argv[1]
    # open up the BiBTeX file and parse it
    with open(bib_database_file_name, encoding="utf-8") as bibtex_file:
        bibliography = bibtexparser.load(bibtex_file)
    # display details about the name of the file
    console.print(
        f":rocket: Always run from root to parse the {bib_database_file_name}"
    )
    console.print(len(bibliography.entries))
    # delete the papers directory if exists;
    # if it does not exist, then create it
    papers_directory = Path("papers/")
    if papers_directory.exists():
        shutil.rmtree(papers_directory)
    else:
        papers_directory.mkdir()
    # create the directories and files for the conference papers
    for publication in bibliography.entries:
        parse_conference_paper(publication)
    console.print()
