"""Parse the bibtex file and create Markdown-based Quarto files for papers and presentations."""

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

GIST_TAG = '<span class="gist">'

RETURN_TO_PAPER_LISTING = (
    "{{< fa circle-left >}} <a href='/research/papers/'>Return to Paper Listing</a>"
)

RETURN_TO_PRESENTATION_LISTING = "{{< fa circle-left >}} <a href='/research/presentations/'>Return to Presentation Listing</a>"

DOWNLOAD_RESEARCH_PAPER_STARTER = "{{< iconify fa6-solid file-pdf >}}"
DOWNLOAD_RESEARCH_PRESENTATION_STARTER = "{{< iconify fa6-solid file-pdf >}}"
DOWNLOAD_SPEAKERDECK_STARTER = "{{< fa brands speaker-deck >}}"
DOWNLOAD_GITHUB_STARTER = "{{< fa brands github >}}"

PAPER_PDF = "paper.pdf"
PRESENTATION_PDF = "presentation.pdf"

PAGE_FULL_ATTRIBUTE = "page-layout: full"

MAX_KEYWORD_SIZE = 3

KEYWORDS_PRESENTATIONS = {
    "Actions": "software tool",
    "annotations": "software testing",
    "application": "software tool",
    "applications": "software tool",
    "automation": "software testing",
    "automated": "software testing",
    "application development": "software development",
    "big data": "database testing",
    "chasten": "software tool",
    "classroom": "undergraduate education",
    "commit messages": "software development",
    "course websites": "undergraduate education",
    "correct software": "software testing",
    "communication": "distributed systems",
    "communication primitive": "distributed systems",
    "creation": "software tool",
    "data": "database testing",
    "database application": "database testing",
    "database applications": "database testing",
    "database interaction": "database testing",
    "distributed systems": "distributed systems",
    "doubling experiments": "performance analysis",
    "efficient": "program performance",
    "efficiency": "program performance",
    "editor": "software tool",
    "exam": "undergraduate education",
    "examinations": "undergraduate education",
    "encourage": "literature review",
    "feedback": "undergraduate education",
    "GitHub": "continuous integration",
    "heaps": "software tool",
    "implementation": "software development",
    "JavaSpace": "distributed systems",
    "Jini": "distributed systems",
    "program instrumentation": "test coverage",
    "measured": "empirical study",
    "measured performance": "performance analysis",
    "measuring the performance": "performance analysis",
    "program": "software tool",
    "programming": "software development",
    "project": "undergraduate education",
    "prioritizers": "test-suite prioritization",
    "pseudo-tested": "mutation testing",
    "Pytest": "software testing",
    "Python": "Python programming",
    "Quarto": "software development",
    "quality": "software testing",
    "regression testing": "test-suite prioritization",
    "software development": "software development",
    "software testing": "software testing",
    "synthetic coverage": "test coverage",
    "teach": "undergraduate education",
    "teaching": "undergraduate education",
    "technique": "software tool",
    "techniques": "software tool",
    "team": "undergraduate education",
    "test suite execution": "test coverage",
    "test execution": "test coverage",
    "test adequacy": "test coverage",
    "testing": "software testing",
    "text": "undergraduate education",
    "time-aware": "performance analysis",
    "text editor": "software development",
    "tuple space": "distributed systems",
    "type annotations": "software development",
    "undergraduates": "undergraduate education",
    "unstructured": "database testing",
    "up and running": "undergraduate education",
    "wrapping": "software development",
}

KEYWORDS_ALL = {
    "applications": "software tool",
    "adequacy criteria": "test coverage",
    "benchmark": "performance analysis",
    "benchmarking": "performance analysis",
    "coverage criteria": "test coverage",
    "coverage effectiveness": "test coverage",
    "current status": "literature review",
    "database-aware": "database testing",
    "database-driven": "database testing",
    "defect prediction": "defect prediction",
    "developer survey": "human study",
    "demonstrations track": "software tool",
    "encourage": "literature review",
    "empirical": "empirical study",
    "empirically": "empirical study",
    "encyclopedia": "literature review",
    "experiment": "empirical study",
    "experiments": "empirical study",
    "execution cost": "performance analysis",
    "execution of regression": "test execution",
    "executing test": "test execution",
    "executing tests": "test execution",
    "experimental study": "empirical study",
    "failure checking": "fault localization",
    "failure detection": "fault localization",
    "fault injection": "mutation testing",
    "test suite health": "mutation testing",
    "flaky": "flaky tests",
    "handbook": "literature review",
    "genetic": "search-based methods",
    "human study": "human study",
    "initial results": "empirical study",
    "invariant": "invariant detection",
    "learned": "undergraduate education",
    "localizing": "fault localization",
    "Jini": "software development",
    "Java framework": "software tool",
    "JavaSpace": "performance analysis",
    "kernel performance": "performance analysis",
    "localiz": "fault localization",
    "machine learning": "machine learning",
    "memory overhead": "performance analysis",
    "multi-source": "empirical study",
    "mutants": "mutation testing",
    "mutation": "mutation testing",
    "prioritizing test suites": "test-suite prioritization",
    "prioritizing tests": "test-suite prioritization",
    "prioritization": "test-suite prioritization",
    "propose": "literature review",
    "pseudo-tested": "mutation testing",
    "PseudoSweep": "test coverage",
    "regression testing": "test-suite prioritization",
    "relational database": "database testing",
    "repair": "program repair",
    "response time": "performance analysis",
    "resource": "performance analysis",
    "reduced test suite": "test-suite reduction",
    "run-time performance": "performance analysis",
    "solution": "software tool",
    "solutions": "software tool",
    "software wrapping": "software tool",
    "study the effectiveness": "empirical study",
    "systems": "software development",
    "testing": "software testing",
    "Testing": "software testing",
    "test data generation": "test-data generation",
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


def create_categories(
    publication: Dict[str, str], is_presentation: bool = False
) -> None:
    """Add categories for a publication since none exist by default in the BiBTeX file."""
    # extract the title and the abstract and the description,
    # if they are available, and use them for category creation
    publication_title = ""
    publication_abstract = ""
    publication_description = ""
    if "title" in publication.keys():
        publication_title = publication["title"]
        publication_title = publication_title.replace("\n", " ")
    if "abstract" in publication.keys():
        publication_abstract = publication["abstract"]
        publication_abstract = publication_abstract.replace("\n", " ")
    if "description" in publication.keys():
        publication_description = publication["description"]
        publication_description = publication_description.replace("\n", " ")
    # designate whether or not anything has been found
    found_keyword = False
    found_keyword_list = []
    # combine the two dictionaries if dealing with a presentation
    # since the paper keywords apply and it is possible to also
    # use any of the keywords for presentations
    if is_presentation:
        keywords = KEYWORDS_ALL | KEYWORDS_PRESENTATIONS
    # not dealing with a presentation so only use the keywords
    # that are general-purpose and geared for papers
    else:
        keywords = KEYWORDS_ALL
    # look to see if each of the specified keywords exists
    # inside of either the title or the abstract; if it
    # does exist, then add it to the list of found keywords
    for current_keyword in keywords.keys():
        if (
            string_found(current_keyword, publication_title)
            or string_found(current_keyword, publication_abstract)
            or string_found(current_keyword, publication_description)
        ):
            found_keyword = True
            found_keyword_list.append(keywords[current_keyword])
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


def create_publication_footer(publication: Dict[str, str], paper: bool = True) -> str:
    """Create a footer for the publications that includes all of the remaining links."""
    # create a running string for the publication footer
    publication_footer = EMPTY
    # only display download details about the paper
    # if they are available for this specific publication
    if "nodownload" not in publication.keys():
        # make a reference to the "get the gist!" if there is
        # markup inside of the abstract to designate that there
        # is a need for the toggle button in the specific file
        get_the_gist_toggle = EMPTY
        if "abstract" in publication.keys():
            # extract the abstract from this publication
            publication_abstract = publication["abstract"]
            # there is a "Get the Gist!" tag inside of the
            # abstract and this means that there should be
            # a toggle button for this publication's description
            if GIST_TAG in publication_abstract:
                get_the_gist_toggle = "{{< include /_gist.qmd >}}"
        # create the details header that will contain
        # the links to different resources for this publication
        details_header = "<div class='quarto-title-details-heading'>Details</div>"
        # extract the identifier for this paper as this is
        # what connects to the name of the files for this paper
        publication_id = publication["ID"]
        # assume that both the paper and the presentation links are
        # empty and then fill them ass appropriate depending on
        # the type of publication for which the script writes the footer
        download_paper = EMPTY
        download_presentation = EMPTY
        # create the links for the paper
        if paper is True:
            # create the links to the presentation based on the ID
            # for each paper; operates under the assumption that every
            # paper will have a link for the paper itself and its slides
            download_paper = (
                f"{DOWNLOAD_RESEARCH_PAPER_STARTER} <a href='/download/research/papers/key/{publication_id}{DASH}{PAPER_PDF}'>Paper</a>"
                + NEWLINE
                + BREAK
            )
            if "presented" in publication.keys():
                download_presentation = (
                    f"{DOWNLOAD_RESEARCH_PRESENTATION_STARTER} <a href='/download/research/presentations/key/{publication_id}{DASH}{PRESENTATION_PDF}'>Presentation</a>"
                    + NEWLINE
                    + BREAK
                )
        # create the link for a presentation
        else:
            # create the links to the presentation based on the ID
            # for the presentation; operates under the assumption that every
            # presentation will have a link for the presentation itself and its slides
            download_presentation = (
                f"{DOWNLOAD_RESEARCH_PRESENTATION_STARTER} <a href='/download/research/presentations/key/{publication_id}{DASH}{PRESENTATION_PDF}'>Presentation</a>"
                + NEWLINE
                + BREAK
            )
        # add the paper and presentation download links to the footer
        publication_footer = (
            get_the_gist_toggle
            + NEWLINE
            + details_header
            + download_paper
            # + NEWLINE
            # + BREAK
            + download_presentation
            # + NEWLINE
            # + BREAK
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
    # define a link label for the listing that will be returned
    # to based on whether this publication is a presentation or
    # a paper; the default parameter's value in a paper
    return_to_listing = ""
    if paper:
        return_to_listing = RETURN_TO_PAPER_LISTING
    else:
        return_to_listing = RETURN_TO_PRESENTATION_LISTING
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
        + return_to_listing
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
    # make sure to use a lower-case directory name to be
    # consistent and to ensure that Quarto correctly
    # resolves all of the categories links from a paper back
    publication_id_lowercase = publication_id.lower()
    papers_directory = Path(f"research/papers/{publication_id_lowercase}/")
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
    # create the categories for the presentation; signal
    # that this is a presentation by the second parameter
    # that is by default going to be false
    create_categories(presentation, is_presentation=True)
    # create the file for this paper in the presentations directory
    # make sure to use a lower-case directory name to be
    # consistent and to ensure that Quarto correctly
    # resolves all of the categories links from a paper back
    presentation_id_lowercase = presentation_id.lower()
    presentations_directory = Path(
        f"research/presentations/{presentation_id_lowercase}/"
    )
    presentations_directory.mkdir(parents=True, exist_ok=True)
    presentation_file = Path(presentations_directory / "index.qmd")
    presentation_file.touch()
    # extract the addendum details
    if "addendum" in presentation.keys():
        presentation_addendum = presentation["addendum"]
        # remove newlines inside of the addendum listing as these will lead
        # to the creation of malformed Markdown meta-data regions when
        # they are used as the list of the authors
        presentation_addendum = presentation_addendum.replace("\n", " ")
        # remove the phrase "Joint work with" as it is not needed for the display
        # of information for this specific presentation (now standardizing on
        # the simple listing of authors and not designating the presenter)
        presentation_addendum = presentation_addendum.replace("Joint work with", "")
        # remove the "and" inside of the joint work listing since we can
        # place the names of authors inside of a list and then they will be
        # rendered correctly by Quarto for this specific presentation
        presentation_addendum = presentation_addendum.replace(", and", ", ")
        # create a list of the authors instead of using a string
        # of author names joined by the word "and"; this will then
        # cause the quarto system to use the label "authors" instead
        # of the singular label "author"
        presentation_author = presentation_addendum + " and " + presentation["author"]
    else:
        # if there was no joint work then this means that there is only a single
        # presenter being listed (i.e., the person who gave the talk which is,
        # in this case, always going to be me) and thus it is the author
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
    # indicate that this is a presentation's footer and not a paper's
    # footer by passing paper=False as the second parameter
    write_file_if_changed(
        str(presentation_file),
        f"---\n{PAGE_FULL_ATTRIBUTE}\n{publication_dump_string}---\n\n{create_publication_footer(presentation, paper=False)}",
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
            publication["description"] = (
                f"<em>{publication_journal}, {publication_volume}:{publication_number}</em>"
            )
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
        # write the publication to the file system
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


def parse_thesis_paper(publication: Dict[str, str]) -> bool:
    """Parse a thesis paper, like a dissertation, noted because it uses a school or institution."""
    if publication.get("school") or publication.get("institution"):
        # extract values from the current publication
        publication_id = publication["ID"]
        publication_year = publication["year"]
        publication_abstract = publication["abstract"]
        publication_booktitle = ""
        if publication.get("school"):
            publication_booktitle = publication["school"]
        elif publication.get("institution"):
            publication_booktitle = publication["institution"]
        # define the description using the "booktitle"
        publication["description"] = f"<em>{publication_booktitle}</em>"
        # write the publication to the file system
        write_publication_to_file(
            publication, publication_abstract, publication_id, publication_year
        )
        return True
    return False


def main() -> None:
    """Perform all of the parsing steps for each bibliography entry."""
    global original_publication  # noqa: PLW0603
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
    if args.bibfile is None:
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
    # delete the research/papers directory if it exists;
    # make sure not to delete any of the files inside of this
    # directory as those could be an index.qmd file with content.
    # Note that the web site's directory structure contains a
    # mixture of generated and manually written content.
    papers_directory = Path("research/papers/")
    if papers_directory.exists() and args.delete:
        console.print(
            ":boom: Deleting the subdirectories in the research/papers/ directory due to --delete\n"
        )
        delete_subdirectories_preserve_files(str(papers_directory))
    # delete the research/presentations directory if it exists;
    # make sure not to delete any of the files inside of this
    # directory as those could be an index.qmd file with content.
    # Note that the web site's directory structure contains a
    # mixture of generated and manually written content.
    presentations_directory = Path("research/presentations/")
    if presentations_directory.exists() and args.delete:
        console.print(
            ":boom: Deleting the subdirectories in the research/presentations/ directory due to --delete\n"
        )
        delete_subdirectories_preserve_files(str(presentations_directory))
    # if the directory does not exist, then create it;
    # this will not fail even if the directory exists. The
    # directory should normally exist because there is a mixture
    # of files that are manually written and generated.
    papers_directory.mkdir(exist_ok=True)
    console.print(
        f":abacus: Found a total of {len(bibliography.entries)} bibliography entries"
    )
    # keep track of the number of conference and journal papers
    # keep track of the number of prsentations
    conference_papers_count = 0
    journal_papers_count = 0
    thesis_papers_count = 0
    presentations_count = 0
    # process all of the entries by creating the directories and files
    # for each one of the relevant bibliography entries
    for publication in bibliography.entries:
        # create a deep copy of the current publication
        # so that there is an object in reserver that
        # was not modified during the parsing process;
        # this version is used for writing out the
        # bibtex entry for each research publication
        original_publication = copy.deepcopy(publication)
        # delete not-needed entries from the original_publication;
        # this is the publication that will be displayed inside of
        # the fenced code block for a specific publication and it
        # does not influence the creation of the actual index.qmd
        # file for this specific publication
        not_needed_keys = [
            "abstract",
            "data",
            "keywords",
            "nodownload",
            "presented",
            "presentation",
            "talk",
            "tool",
            "video",
        ]
        for not_needed_key in not_needed_keys:
            if not_needed_key in original_publication.keys():
                del original_publication[not_needed_key]
        # --> for the conference papers
        if parse_conference_paper(publication):
            conference_papers_count = conference_papers_count + 1
        # --> for the journal papers
        if parse_journal_paper(publication):
            journal_papers_count = journal_papers_count + 1
        # --> for the journal papers
        if parse_thesis_paper(publication):
            thesis_papers_count = thesis_papers_count + 1
        # --> for the presentations
        if parse_presentation(publication):
            presentations_count = presentations_count + 1
    # display final diagnostic information about the
    # execution of the script, in terms of counts of entities
    console.print()
    console.print(
        f":tada: Parsed {conference_papers_count} conference papers, {journal_papers_count} journal papers, {thesis_papers_count} theses, and {presentations_count} presentations"
    )


if __name__ == "__main__":
    # display the path of the python executable
    # run the main function
    # that controls all of the parsing
    # of the bibliography entries
    main()
