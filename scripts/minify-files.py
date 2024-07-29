"""Minify all of the files in the project."""

import argparse
import datetime
import os
import shutil
import sys
from pathlib import Path

import csscompressor
import minify_html
import rjsmin
from rich.console import Console

console = Console()

DEFAULT_CONSOLE_STYLE = "bold blue"

source_directory_root = ""


def display_file_sizes(original_size: int, minified_size: int, type: str) -> None:
    """Display the file sizes and information about their differences."""
    # calculate the reduction in size and the percentage reduction in size
    reduction = original_size - minified_size
    percentage_reduction = (reduction / original_size) * 100
    # display diagnostic information about the minification process
    console.print(f"{type}: File Size Savings: {reduction} bytes")
    console.print(
        f"{type}: Percentage Reduction in File Size: {percentage_reduction:.2f}%"
    )
    console.print()


def minify_files(source_directory: str, destination_directory: str) -> None:
    """Minify all of the files in the project directory."""
    # global source_directory_root
    # recursively iterate through all files and directories
    for current_file_name in os.listdir(source_directory):
        # create the current filename subject to analysis
        analysis_file_path = os.path.join(source_directory, current_file_name)
        # dealing with a file and thus it is a candidate
        # for the minification process
        if os.path.isfile(analysis_file_path):
            # create the current filename for writing to file system
            saving_file_path_str = analysis_file_path
            saving_file_path_str = saving_file_path_str.replace(
                source_directory_root, destination_directory
            )
            destination_path = Path(saving_file_path_str)
            # create the destination directory if it doesn't exist
            destination_path.parent.absolute().mkdir(parents=True, exist_ok=True)
            # extract the extension from this filename so
            # that the script can check if it is one of
            # the types of files that can be minified
            extension = os.path.splitext(current_file_name)[1].lower()
            # minify the CSS file
            if extension == ".css":
                # only minify a file that does not exist inside of the site_libs;
                # note that there is a font-awesome CSS file inside of the site_libs
                # that is not already minified and thus some content is bigger than
                # needed; leave this optimization for later as it is not critical
                try:
                    original_content = open(analysis_file_path).read()
                    original_size = len(original_content)
                    minified_content = csscompressor.compress(original_content)
                    minified_size = len(minified_content)
                    # set the file permissions to be writable (note that the files
                    # that are a part of site_libs are not writable by default)
                    os.chmod(saving_file_path_str, 0o600)
                    with open(saving_file_path_str, "w") as file:
                        file.write(minified_content)
                    console.print(f"CSS: Minifying {analysis_file_path}")
                    console.print(f"CSS: Saving {saving_file_path_str}")
                    display_file_sizes(original_size, minified_size, "CSS")
                except ValueError:
                    console.print(f"CSS: Could not minify file {analysis_file_path}")
                    console.print()
            # minify the HTML file
            elif extension == ".html":
                # minify the HTML file using the minify_html package;
                # note that this package uses other underlying tools
                # and rust to minify the HTML file
                try:
                    # read the original content of the file and
                    # calculate the size of the original content
                    original_content = open(analysis_file_path).read()
                    original_size = len(original_content)
                    minified_content = minify_html.minify(
                        original_content,
                        minify_js=True,
                        minify_css=True,
                        keep_comments=False,
                        keep_closing_tags=True,
                        keep_spaces_between_attributes=True,
                    )
                    # calculate the size of the minified content
                    minified_size = len(minified_content)
                    # save the minified content to the destination file
                    with open(saving_file_path_str, "w") as file:
                        file.write(minified_content)
                    console.print(f"HTML: Minifying {analysis_file_path}")
                    console.print(f"HTML: Saving {saving_file_path_str}")
                    # display diagnostic information about the minification process
                    display_file_sizes(original_size, minified_size, "HTML")
                except Exception as e:
                    console.print(f"HTML: Could not minify file {analysis_file_path}")
                    console.print(f"HTML: Exception {e}")
                    console.print()
                    continue
            # minify the JS file using the rjsmin package
            elif extension == ".js":
                # do not minify a file that exists inside of the site_libs
                # directory as it is a file that should not be minified
                original_content = open(analysis_file_path).read()
                original_size = len(original_content)
                minified_content = str(rjsmin.jsmin(original_content))
                minified_size = len(minified_content)
                # set the file permissions to be writable (note that the files
                # that are a part of site_libs are not writable by default)
                os.chmod(saving_file_path_str, 0o600)
                with open(saving_file_path_str, "w") as file:
                    file.write(minified_content)
                console.print(f"JS: Minifying {analysis_file_path}")
                console.print(f"JS: Saving to {saving_file_path_str}")
                display_file_sizes(original_size, minified_size, "JS")
            # do not have a minifier for a specific
            # file and thus this file should be skipped
            else:
                console.print(f"Skipping {analysis_file_path}")
                console.print()
        # found a directory, so recursively traverse into
        # so that minification process can continue until done;
        # keep using the same destination_directory as that will
        # not change during the recursive traversal process
        elif os.path.isdir(analysis_file_path):
            minify_files(analysis_file_path, destination_directory)


def main() -> None:
    """Perform the steps for the main function."""
    global source_directory_root  # noqa: PLW0603
    # parse the command-line arguments using argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source")
    parser.add_argument("-d", "--destination")
    parser.add_argument("-f", "--force", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    # create the argument parser
    args = parser.parse_args()
    # do not run the script unless quarto is rendering
    # all of the files (i.e., do not run during preview)
    if not os.getenv("QUARTO_PROJECT_RENDER_ALL") and not args.force:
        sys.exit()
    # define the default source directory that will contain
    # the contents that are going to be minified
    source_directory_path = "_site"
    # define the default destination directory that will
    # contain the minified contents
    destination_directory_path = "_site"
    # there is a directory for the source, so use it instead of
    # the default directory for the source
    if args.source is not None:
        source_directory_path = args.source
    # there is a directory for the destination, so use it instead of
    # the default directory for the destination
    if args.destination is not None:
        destination_directory_path = args.destination
    # provide the debugging information
    if args.verbose is True:
        console.print(
            f":clap: Using the destination directory of {destination_directory_path}\n",
            style=DEFAULT_CONSOLE_STYLE,
        )
        console.print(
            f":clap: Using the source directory of {source_directory_path}\n",
            style=DEFAULT_CONSOLE_STYLE,
        )
    # define the global source directory root
    source_directory_root = source_directory_path
    # create a backup of the destination directory
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    backup_directory_path = f"{destination_directory_path}_backup_{timestamp}"
    shutil.copytree(destination_directory_path, backup_directory_path)
    console.print(
        f"Created a backup of the destination directory at {backup_directory_path}"
    )
    console.print()
    # perform the minification of all of the files
    # inside of the directory; note that this is
    # a destructive operation that changes the
    # contents of the specified directory
    minify_files(source_directory_path, destination_directory_path)
    # console.print()


if __name__ == "__main__":
    # run the main function
    # that controls all of the minification
    # steps (e.g., minify CSS, HTML, and JS)
    main()
