"""Parse the bibtex file."""

import argparse
import re
import shutil
from pathlib import Path
from typing import Dict

import bibtexparser
import yaml
from rich.console import Console

console = Console()

KEYWORDS = {
    "relational database": "database testing",
    "developer survey": "developer survey",
    "empirical": "empirical study",
    "experiment": "empirical study",
    "flaky": "flaky tests",
    "generate": "test-data generation",
    "genetic": "search-based methods",
    "invariant": "invariant detection",
    "localiz": "fault localization",
    "mutation": "mutation testing",
    "prioritization": "test-suite prioritization",
    "reduction": "test-suite reduction",
    "schema": "database testing",
    "SchemaAnalyst": "database testing",
    "search": "search-based methods",
    "SBST": "search-based methods",
    "survey": "literature review",
    "time overhead": "program performance",
    "web": "web testing",
    "unstructured": "program performance",
}


def string_found(search_string: str, containing_string: str) -> bool:
    """Determine if the first string is inside of the major string."""
    if re.search(r"\b" + re.escape(search_string) + r"\b", containing_string):
        return True
    return False


def create_categories(publication: Dict[str, str]) -> None:
    """Add categories for a publication since none exist by default in the BiBTeX file."""
    # extract the title and the abstract
    publication_title = publication["title"]
    publication_abstract = publication["abstract"]
    # designate whether or not anything has been found
    found_keyword = False
    found_keyword_list = []
    # look to see if each of the specified keywords exists
    # inside of either the title or the abstract; if it
    # does exist, then add it to the list of found keywords
    for current_keyword in KEYWORDS.keys():
        if (
            string_found(current_keyword, publication_title)
            or string_found(current_keyword, publication_abstract)
        ):
            found_keyword = True
            found_keyword_list.append(KEYWORDS[current_keyword])
    # at least one keyword was found, so create a new key value
    # pair entry inside of the publication provided as the input
    if found_keyword:
        publication["categories"] = f"[{', '.join(found_keyword_list)}]"


def parse_conference_paper(publication: Dict[str, str]) -> None:
    """Parse a conference paper, noted because it uses a booktitle."""
    if publication.get("booktitle"):
        # print("Found something!")
        # extract values from the current publication
        publication_id = publication["ID"]
        publication_year = publication["year"]
        publication_abstract = publication["abstract"]
        publication_booktitle = publication["booktitle"]
        # console.print(publication_id)
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
        # create the categories
        create_categories(publication)
        # create the file for this paper in the papers directory
        papers_directory = Path(f"papers/{publication_year}-{publication_id}/")
        papers_directory.mkdir(parents=True, exist_ok=True)
        publication_file = Path(papers_directory / "index.qmd")
        publication_file.touch()
        # dump the publication dictionary to a string and then patch up
        # the string so that the categories are formatted correctly
        publication_dump_string = yaml.dump(
            publication, allow_unicode=True, default_flow_style=False
        )
        publication_dump_string = publication_dump_string.replace("'[", "[")
        publication_dump_string = publication_dump_string.replace("]'", "]")
        # write the complete contents of the string to the designated file
        publication_file.write_text(
            f"---\n{publication_dump_string}---",
            encoding="utf-8",
        )


if __name__ == "__main__":
    # display the command-line arguments
    # print(f"Arguments count: {len(sys.argv)}")
    # for i, argument in enumerate(sys.argv):
    # print(f"Argument {i:>6}: {argument}")
    # parse the arguments using argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--bibfile")
    parser.add_argument("-d", "--delete", action="store_true")
    args = parser.parse_args()
    # determine whether to use the default bibliography
    # (if one is not specified) or to use a specified
    # one, normally provided for testing purposes
    bibliography = None
    # print(args)
    console.print()
    if args.bibfile == None:
        console.print(":clap: Using the default bibliography file of bibliography/bibtex/bibliography_kapfhammer.bib\n")
        bib_database_file_name = "bibliography/bibtex/bibliography_kapfhammer.bib"
    else:
        console.print(":clap: Using {args.bibfile} as specified by --bibfile")
        bib_database_file_name = args.bibfile
    # open up the BiBTeX file and parse it
    with open(bib_database_file_name, encoding="utf-8") as bibtex_file:
        bibliography = bibtexparser.load(bibtex_file)
    # delete the papers directory if exists;
    # if it does not exist, then create it
    papers_directory = Path("papers/")
    if papers_directory.exists() and args.delete:
        console.print(":boom: Deleting the papers directory due to --delete\n")
        shutil.rmtree(papers_directory)

    papers_directory.mkdir(exist_ok=True)
    console.print(f":abacus: Found a total of {len(bibliography.entries)} bibliography entries")
    # process all of the entries by create the directories and files for the conference papers
    for publication in bibliography.entries:
        parse_conference_paper(publication)
    console.print()
