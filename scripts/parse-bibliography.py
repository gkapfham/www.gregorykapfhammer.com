"""Parse the bibtex file."""

import argparse
import copy
import hashlib
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Dict

import bibtexparser
import yaml
from bibtexparser.bibdatabase import BibDatabase
from rich.console import Console

console = Console()

original_publication = {}

BREAK = "<br>"
DASH = "-"
EMPTY = ""
NEWLINE = "\n"
SPACE = " "

RETURN_TO_PAPER_LISTING = (
    "{{< fa circle-left >}} <a href='/research/papers/'>Return to Paper Listing</a>"
)

DOWNLOAD_PUBLICATION_STARTER = "{{< fa file-pdf >}}"
DOWNLOAD_SPEAKERDECK_STARTER = "{{< fa brands speaker-deck >}}"
DOWNLOAD_GITHUB_STARTER = "{{< fa brands github >}}"

PAPER_PDF = "paper.pdf"
PRESENTATION_PDF = "presentation.pdf"

PAGE_FULL_ATTRIBUTE = "page-layout: full"

MAX_KEYWORD_SIZE = 3

KEYWORDS = {
    "adequacy criteria": "test coverage",
    "database-aware": "database testing",
    "defect prediction": "defect prediction",
    "developer survey": "human study",
    "demonstrations track": "software tool",
    "empirical": "empirical study",
    "empirically": "empirical study",
    "encyclopedia": "literature review",
    "experiment": "empirical study",
    "execution cost": "performance analysis",
    "execution of regression": "test execution",
    "executing test": "test execution",
    "executing tests": "test execution",
    "experimental study": "empirical study",
    "flaky": "flaky tests",
    "handbook": "literature review",
    "genetic": "search-based methods",
    "human study": "human study",
    "invariant": "invariant detection",
    "JavaSpace": "performance analysis",
    "kernel performance": "performance analysis",
    "localiz": "fault localization",
    "machine learning": "machine learning",
    "memory overhead": "performance analysis",
    "mutation": "mutation testing",
    "prioritizing test suites": "test-suite prioritization",
    "prioritizing tests": "test-suite prioritization",
    "prioritization": "test-suite prioritization",
    "relational database": "database testing",
    "repair": "program repair",
    "response time": "performance analysis",
    "reduced test suite": "test-suite reduction",
    "test generation": "test-data generation",
    "test reduction": "test-suite reduction",
    "test suite reduction": "test-suite reduction",
    "time complexity": "performance analysis",
    "tool": "software tool",
    "schema": "database testing",
    "SchemaAnalyst": "database testing",
    "search": "search-based methods",
    "survey of": "literature review",
    "SBST": "search-based methods",
    "test coverage": "test coverage",
    "time overhead": "performance analysis",
    "web page": "web testing",
    "web pages": "web testing",
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
    if re.search(
        r"\b" + re.escape(search_string.lower()) + r"\b", containing_string.lower()
    ):
        return True
    return False


def replace_word_in_string(search_string: str, old_word: str, new_word: str) -> str:
    """Replace a word in a string while respecting string boundaries."""
    pattern = r"\b" + re.escape(old_word) + r"\b"
    replaced_string = re.sub(pattern, new_word, search_string)
    return replaced_string


def create_categories(publication: Dict[str, str]) -> None:
    """Add categories for a publication since none exist by default in the BiBTeX file."""
    # extract the title and the abstract and the description,
    # if they are available, and use them for category creation
    publication_title = ""
    publication_abstract = ""
    publication_description = ""
    if "title" in publication.keys():
        publication_title = publication["title"]
    if "abstract" in publication.keys():
        publication_abstract = publication["abstract"]
    if "description" in publication.keys():
        publication_description = publication["description"]
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
            or string_found(current_keyword, publication_description)
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


def create_publication_footer(publication: Dict[str, str]) -> str:
    """Create a footer for the publications that includes all of the remaining links."""
    global orignal_entry
    # create a running string for the publication footer
    publication_footer = EMPTY
    # only display download details about the paper
    # if they are available for this specific publication
    if "nodownload" not in publication.keys():
        # create the details header that will contain
        # the links to different resources for this publication
        details_header = "<div class='quarto-title-details-heading'>Details</div>"
        # extract the identifier for this paper as this is
        # what connects to the name of the files for this paper
        publication_id = publication["ID"]
        # create the links to the presentation based on the ID
        # for each paper; operates under the assumption that every
        # paper will have a link for the paper itself and its slides
        download_paper = f"{DOWNLOAD_PUBLICATION_STARTER} <a href='/research/papers/key/{publication_id}{DASH}{PAPER_PDF}'>Paper</a>"
        download_presentation = f"{DOWNLOAD_PUBLICATION_STARTER} <a href='/research/presentations/key/{publication_id}{DASH}{PRESENTATION_PDF}'>Presentation</a>"
        # add the paper and presentation download links to the footer
        publication_footer = (
            details_header
            + download_paper
            + NEWLINE
            + BREAK
            + download_presentation
            + NEWLINE
            + BREAK
        )
        # if the paper has details about the SpeakerDeck link
        # for its presentation slides, then add them to the footer
        if "presentation" in publication.keys():
            publication_footer = (
                publication_footer
                + DOWNLOAD_SPEAKERDECK_STARTER
                + SPACE
                + f"<a href='{publication['presentation']}'>Presentation</a>"
                + NEWLINE
                + BREAK
            )
        # if the paper has details about GitHub for a data set,
        # then add it to the footer; note that it will only add
        # the "GitHub repo" name for the link content
        if "data" in publication.keys():
            repository_name = publication["data"].replace("https://github.com/", "")
            publication_footer = (
                publication_footer
                + DOWNLOAD_GITHUB_STARTER
                + SPACE
                + f"<a href='{publication['data']}'> {repository_name}</a>"
                + NEWLINE
                + BREAK
            )
        # if the paper has details about GitHub for a tool,
        # then add it to the footer; note that it will only add
        # the "GitHub repo" name for the link content
        if "tool" in publication.keys():
            repository_name = publication["tool"].replace("https://github.com/", "")
            publication_footer = (
                publication_footer
                + DOWNLOAD_GITHUB_STARTER
                + SPACE
                + f"<a href='{publication['tool']}'> {repository_name}</a>"
                + NEWLINE
            )
    # create a header for the segment of the page that will display the
    # bibtex reference for the paper currently being parsed
    bibtex_reference_header = (
        "<div class='quarto-title-reference-heading'>Reference</div>"
    )
    # re-created the bibtex entry from the dictionary of the entry
    db = BibDatabase()
    db.entries = [original_publication]
    bibtex_reference = bibtexparser.dumps(db)
    # create a fenced code block out of the bibtex entry
    bibtex_reference_fenced_code_block = f"```bibtex{NEWLINE}{bibtex_reference}```"
    # assemble the entire footer for this specific publication
    publication_footer = (
        publication_footer
        + NEWLINE
        + NEWLINE
        + NEWLINE
        + bibtex_reference_header
        + NEWLINE
        + bibtex_reference_fenced_code_block
        + NEWLINE
        + RETURN_TO_PAPER_LISTING
    )
    # return the footer for this publication
    return publication_footer


def write_publication_to_file(
    publication: Dict[str, str],
    publication_abstract: str,
    publication_id: str,
    publication_year: str,
) -> None:
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
    papers_directory = Path(f"research/papers/{publication_id}/")
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
        str(publication_file),
        f"---\n{PAGE_FULL_ATTRIBUTE}\n{publication_dump_string}---\n\n{create_publication_footer(publication)}",
    )


def write_presentation_to_file(
    presentation: Dict[str, str], presentation_id: str, presentation_year: str
) -> None:
    """Write the details about a publication to the specified file."""
    # define the date so that it is a string in YYYY-MM-DD format;
    # note that this sets up the date so that the MM and the DD
    # will be ignored later as conference papers do not need MM or DD
    presentation_year = presentation["year"]
    del presentation["year"]
    presentation["date"] = f"{presentation_year}-01-01"
    # define the date-format to only display the year
    only_year = "YYYY"
    presentation["date-format"] = f"{only_year}"
    # create the categories
    create_categories(presentation)
    # create the file for this paper in the papers directory
    presentations_directory = Path(f"research/presentations/{presentation_id}/")
    presentations_directory.mkdir(parents=True, exist_ok=True)
    presentation_file = Path(presentations_directory / "index.qmd")
    presentation_file.touch()
    # extract the addendum details
    if "addendum" in presentation.keys():
        presentation_addendum = presentation["addendum"]
        console.print(presentation_addendum)
        presentation_addendum = presentation_addendum.replace("Joint work with", "")
        presentation_addendum = presentation_addendum.replace(", and", ", ")
        # create a list of the authors instead of using a string
        # of author names joined by the word "and"; this will then
        # cause the quarto system to use the label "authors" instead
        # of the singular label "author"
        presentation_author = presentation_addendum + " and " + presentation["author"]
    else:
        presentation_author = presentation["author"]
    # create the listing of the authors separated with commas in a list
    publication_author_no_and = replace_word_in_string(presentation_author, "and", ",")
    presentation_author = f"[{publication_author_no_and}]"
    presentation["author"] = presentation_author
    # dump the publication dictionary to a string and then patch up
    # the string so that the categories are formatted correctly
    publication_dump_string = yaml.dump(
        presentation, allow_unicode=True, default_flow_style=False
    )
    publication_dump_string = publication_dump_string.replace("'[", "[")
    publication_dump_string = publication_dump_string.replace("]'", "]")
    # write the complete contents of the string to the designated file
    write_file_if_changed(
        str(presentation_file),
        f"---\n{PAGE_FULL_ATTRIBUTE}\n{publication_dump_string}---\n\n{create_publication_footer(presentation)}",
    )


def delete_subdirectories_preserve_files(directory: str) -> None:
    """Delete all sub-directories below the specified directory."""
    for root, dirs, _ in os.walk(directory, topdown=False):
        for name in dirs:
            path = os.path.join(root, name)
            if os.path.isdir(path):
                shutil.rmtree(path)


def parse_journal_paper(publication: Dict[str, str]) -> bool:
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
            publication[
                "description"
            ] = f"<em>{publication_journal}, {publication_volume}:{publication_number}</em>"
        # there is no volume and/or number and thus the description
        # of this publication should only be the name of the journal
        else:
            publication["description"] = f"<em>{publication_journal}</em>"
        # write the publication to the file system
        write_publication_to_file(
            publication, publication_abstract, publication_id, publication_year
        )
        return True
    return False


def parse_conference_paper(publication: Dict[str, str]) -> bool:
    """Parse a conference paper, noted because it uses a booktitle."""
    if publication.get("booktitle"):
        # extract values from the current publication
        publication_id = publication["ID"]
        publication_year = publication["year"]
        publication_abstract = publication["abstract"]
        publication_booktitle = publication["booktitle"]
        # define the description using the booktitle
        publication["description"] = f"<em>{publication_booktitle}</em>"
        # write the publication to the file systems
        write_publication_to_file(
            publication, publication_abstract, publication_id, publication_year
        )
        return True
    return False


def parse_presentation(publication: Dict[str, str]) -> bool:
    """Parse a prsentation, noted by the fact that it uses a howpublished."""
    if publication.get("howpublished"):
        # extract values from the current presentation
        publication_id = publication["ID"]
        publication_year = publication["year"]
        publication_presentation_venue = publication["howpublished"]
        # define the description using the howpublished, which is
        # the venue of the presentation
        publication["description"] = f"<em>{publication_presentation_venue}</em>"
        # write the publication to the file systems
        write_presentation_to_file(publication, publication_id, publication_year)
        return True
    return False


def main() -> None:
    """Perform the operations of the main function."""
    global original_publication
    # parse the command-line arguments using argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--bibfile")
    parser.add_argument("-d", "--delete", action="store_true")
    parser.add_argument("-f", "--force", action="store_true")
    args = parser.parse_args()
    # display a blank line to ensure better formatting
    console.print()
    # do not run the script unless quarto is rendering
    # all of the files (i.e., do not run during preview)
    if not os.getenv("QUARTO_PROJECT_RENDER_ALL") and not args.force:
        sys.exit()
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
    # delete the research/papers directory if exists;
    # make sure not to delete any of the files inside of this
    # directory as those could be an index.qmd file with content
    papers_directory = Path("research/papers/")
    if papers_directory.exists() and args.delete:
        console.print(
            ":boom: Deleting the subdirectories in the research/papers/ directory due to --delete\n"
        )
        delete_subdirectories_preserve_files(str(papers_directory))
    # if the directory does not exist, then create it;
    # this will not fail even if the directory exists, which it should
    papers_directory.mkdir(exist_ok=True)
    console.print(
        f":abacus: Found a total of {len(bibliography.entries)} bibliography entries"
    )
    # keep track of the number of conference and journal papers
    conference_papers_count = 0
    journal_papers_count = 0
    presentations_count = 0
    # process all of the entries by create the directories and files
    for publication in bibliography.entries:
        original_publication = copy.deepcopy(publication)
        if "abstract" in original_publication.keys():
            del original_publication["abstract"]
        # --> for the conference papers
        if parse_conference_paper(publication):
            conference_papers_count = conference_papers_count + 1
        # --> for the journal papers
        if parse_journal_paper(publication):
            journal_papers_count = journal_papers_count + 1
        # --> for the presentations
        if parse_presentation(publication):
            presentations_count = presentations_count + 1
    console.print()
    console.print(
        f":tada: Parsed {conference_papers_count} conference papers, {journal_papers_count} journal papers, and {presentations_count} presentations"
    )


if __name__ == "__main__":
    main()
