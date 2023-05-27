"""Parse the bibtex file."""

import argparse
import hashlib
import re
import shutil
from pathlib import Path
from typing import Dict

import bibtexparser
import yaml
from rich.console import Console

console = Console()

MAX_KEYWORD_SIZE = 4

KEYWORDS = {
    "adequacy criteria": "test coverage",
    "defect prediction": "defect prediction",
    "developer survey": "human study",
    "empirical": "empirical study",
    "empirically": "empirical study",
    "Encyclopedia": "literature review",
    "experiment": "empirical study",
    "execution of regression": "test execution",
    "executing test": "test execution",
    "executing tests": "test execution",
    "flaky": "flaky tests",
    "generation": "test-data generation",
    "genetic": "search-based methods",
    "human study": "human study",
    "invariant": "invariant detection",
    "JavaSpace": "performance analysis",
    "localiz": "fault localization",
    "memory overhead": "performance analysis",
    "mutation": "mutation testing",
    "prioritizing test suites": "test-suite prioritization",
    "prioritizing tests": "test-suite prioritization",
    "prioritization": "test-suite prioritization",
    "relational database": "database testing",
    "repair": "program repair",
    "reduced test suite": "test-suite reduction",
    "test reduction": "test-suite reduction",
    "test suite reduction": "test-suite reduction",
    "time complexity": "performance analysis",
    "tool": "software tool",
    "schema": "database testing",
    "SchemaAnalyst": "database testing",
    "search": "search-based methods",
    "SBST": "search-based methods",
    "survey": "literature review",
    "test coverage": "test coverage",
    "time overhead": "performance analysis",
    "web page": "web testing",
    "web site": "web testing",
    "unstructured": "performance analysis",
}


def write_file_if_changed(file_path: str, content: str) -> None:
    """Write the file to the filesystem only when it contents differ from current file."""
    # Create a Path object from the file path
    path = Path(file_path)
    # Calculate the hash of the new content
    new_content_hash = hashlib.md5(content.encode()).hexdigest()
    # Check if the file exists and calculate the hash of its current content
    if path.exists():
        with path.open(mode="r") as file:
            current_content = file.read()
            current_content_hash = hashlib.md5(current_content.encode()).hexdigest()
            # If the content hashes match, no need to write the file again
            if new_content_hash == current_content_hash:
                return
    # Write the new content to the file
    with path.open(mode="w") as file:
        file.write(content)


def delete_elements_beyond_max_size(provided_list: list, max_size: int) -> None:
    """Delete elements from a list beyond a maximum size."""
    # extract the length of the list and then remove
    # all of the elements in the list beyond the maximum size;
    # note that, for now, this function is useful to ensure that
    # none of the publications etc. have more than a max_size number
    # of categories associated with them. It is also important to
    # note that, for now, the assumption is that this function will
    # always accept elements that are ordered according to some
    # priority where the most "important" elements are earlier in the list 
    length_provided_list = len(provided_list)
    if length_provided_list > max_size:
        del provided_list[max_size:]


def string_found(search_string: str, containing_string: str) -> bool:
    """Determine if the first string is inside of the major string."""
    # determine whether or not the containing_string contains the search_string,
    # factoring in the fact that this will ignore spacing and other issues and
    # ultimately be, most likely, more robust that using the "in" keyword
    if re.search(r"\b" + re.escape(search_string.lower()) + r"\b", containing_string.lower()):
        return True
    return False


def replace_word_in_string(string, old_word, new_word):
    """Replace a word in a string while respecting string boundaries."""
    pattern = r"\b" + re.escape(old_word) + r"\b"
    replaced_string = re.sub(pattern, new_word, string)
    return replaced_string


def create_categories(publication: Dict[str, str]) -> None:
    """Add categories for a publication since none exist by default in the BiBTeX file."""
    # extract the title and the abstract
    publication_title = publication["title"]
    publication_abstract = publication["abstract"]
    # publication_booktitle = publication["booktitle"]
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
            # or string_found(current_keyword, publication_booktitle)
        ):
            found_keyword = True
            found_keyword_list.append(KEYWORDS[current_keyword])
    # at least one keyword was found, so create a new key value
    # pair entry inside of the publication provided as the input
    if found_keyword:
        # remove any of the duplicates inside of the list of keywords
        found_keyword_set = set(found_keyword_list)
        found_keyword_list = list(found_keyword_set)
        # sort the list alphabetically
        found_keyword_list.sort()
        # do not allow more than four entries for keywords
        delete_elements_beyond_max_size(found_keyword_list, MAX_KEYWORD_SIZE)
        publication["categories"] = f"[{', '.join(found_keyword_list)}]"


def write_publication_to_file(publication: Dict[str, str], publication_abstract, publication_id, publication_year):
    """Write the details about a publication to the specified file."""
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
    # create a list of the authors instead of using a string
    # of author names joined by the word "and"; this will then
    # cause the quarto system to use the label "authors" instead
    # of the singular label "author"
    publication_author = publication["author"]
    publication_author_no_and = replace_word_in_string(publication_author, "and", ",")
    publication_author = f"[{publication_author_no_and}]"
    publication["author"] = publication_author
    # dump the publication dictionary to a string and then patch up
    # the string so that the categories are formatted correctly
    publication_dump_string = yaml.dump(
        publication, allow_unicode=True, default_flow_style=False
    )
    publication_dump_string = publication_dump_string.replace("'[", "[")
    publication_dump_string = publication_dump_string.replace("]'", "]")
    # write the complete contents of the string to the designated file
    write_file_if_changed(
        str(publication_file), f"---\n{publication_dump_string}---"
    )


def parse_journal_paper(publication: Dict[str, str]) -> None:
    """Parse a journal paper, noted because it features an attribut called a journal."""
    # dealing with a journal publication that is not one of the edited volumes
    if publication.get("journal") and not publication.get("keywords") == "edit":
        # extract values from the current publication
        publication_id = publication["ID"]
        publication_year = publication["year"]
        publication_abstract = publication["abstract"]
        publication_journal = publication["journal"]
        del publication["journal"]
        # create the description of the journal publication using
        # the name of the journal and the volume and number
        if publication.get("volume") and publication.get("number"):
            publication_volume = publication["volume"]
            publication_number = publication["number"]
            # define the description using the booktitle
            publication["description"] = f"<em>{publication_journal}, {publication_volume}:{publication_number}</em>"
        # there is no volume and/or number and thus the description
        # of this publication should only be the name of the journal
        else:
            publication["description"] = f"<em>{publication_journal}</em>"
        write_publication_to_file(publication, publication_abstract, publication_id, publication_year)


def parse_conference_paper(publication: Dict[str, str]) -> None:
    """Parse a conference paper, noted because it uses a booktitle."""
    if publication.get("booktitle"):
        # extract values from the current publication
        publication_id = publication["ID"]
        publication_year = publication["year"]
        publication_abstract = publication["abstract"]
        publication_booktitle = publication["booktitle"]
        # console.print(publication_id)
        # define the description using the booktitle
        publication["description"] = f"<em>{publication_booktitle}</em>"
        write_publication_to_file(publication, publication_abstract, publication_id, publication_year)

        # # redefine the abstract so that there are no newlines in it
        # publication_abstract = publication_abstract.replace("\n", " ")
        # publication["abstract"] = publication_abstract
        # # define the date so that it is a string in YYYY-MM-DD format;
        # # note that this sets up the date so that the MM and the DD
        # # will be ignored later as conference papers do not need MM or DD
        # publication_year = publication["year"]
        # del publication["year"]
        # publication["date"] = f"{publication_year}-01-01"
        # # define the date-format to only display the year
        # only_year = "YYYY"
        # publication["date-format"] = f"{only_year}"
        # # create the categories
        # create_categories(publication)
        # # create the file for this paper in the papers directory
        # papers_directory = Path(f"papers/{publication_year}-{publication_id}/")
        # papers_directory.mkdir(parents=True, exist_ok=True)
        # publication_file = Path(papers_directory / "index.qmd")
        # publication_file.touch()
        # # create a list of the authors instead of using a string
        # # of author names joined by the word "and"; this will then
        # # cause the quarto system to use the label "authors" instead
        # # of the singular label "author"
        # publication_author = publication["author"]
        # publication_author_no_and = replace_word_in_string(publication_author, "and", ",")
        # publication_author = f"[{publication_author_no_and}]"
        # publication["author"] = publication_author
        # console.print(publication_author)
        # # console.print(publication_author)
        # # dump the publication dictionary to a string and then patch up
        # # the string so that the categories are formatted correctly
        # publication_dump_string = yaml.dump(
        #     publication, allow_unicode=True, default_flow_style=False
        # )
        # publication_dump_string = publication_dump_string.replace("'[", "[")
        # publication_dump_string = publication_dump_string.replace("]'", "]")
        # # write the complete contents of the string to the designated file
        # write_file_if_changed(
        #     str(publication_file), f"---\n{publication_dump_string}---"
        # )


if __name__ == "__main__":
    # parse the command-line arguments using argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--bibfile")
    parser.add_argument("-d", "--delete", action="store_true")
    args = parser.parse_args()
    # display a blank line to ensure better formatting
    console.print()
    # determine whether to use the default bibliography
    # (if one is not specified) or to use a specified
    # one, normally provided for testing purposes
    bibliography = None
    if args.bibfile == None:
        console.print(
            ":clap: Using the default bibliography file of bibliography/bibtex/bibliography_kapfhammer.bib\n"
        )
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
    console.print(
        f":abacus: Found a total of {len(bibliography.entries)} bibliography entries"
    )
    # process all of the entries by create the directories and files for the conference papers
    for publication in bibliography.entries:
        parse_conference_paper(publication)
        parse_journal_paper(publication)
    console.print()
