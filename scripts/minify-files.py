"""Minify all of the files in the project."""

import argparse
import os
import sys

import csscompressor
import htmlmin
import rjsmin
from rich.console import Console

console = Console()


def minify_files(directory):
    """Minify all of the files in the project directory."""
    # recursively iterate through all files and directories
    for filename in os.listdir(directory):
        # extract the current filename
        filepath = os.path.join(directory, filename)
        # dealing with a file and thus it is a candidate
        # for the minification process
        if os.path.isfile(filepath):
            # extract the extension from this filename so
            # that the script can check if it is one of
            # the types of files that can be minified
            extension = os.path.splitext(filename)[1].lower()
            # minify the CSS file
            if extension == ".css":
                try:
                    minified_content = csscompressor.compress(open(filepath).read())
                    with open(filepath, "w") as file:
                        file.write(minified_content)
                    console.print(f"CSS {filepath} minified")
                except ValueError:
                    console.print(f"Could not minifiy file {filepath}")
            # minify the HTML file
            elif extension == ".html":
                minified_content = htmlmin.minify(
                    open(filepath).read(),
                    remove_comments=True,
                    remove_empty_space=True,
                )
                with open(filepath, "w") as file:
                    file.write(minified_content)
                console.print(f"HTML {filepath} minified")
            # minify the JS file
            elif extension == ".js":
                minified_content = str(rjsmin.jsmin(open(filepath).read()))
                with open(filepath, "w") as file:
                    file.write(minified_content)
                console.print(f"JS {filepath} minified")
            # do not have a minifier for a specific
            # file and thus this file should be skipped
            else:
                console.print(f"{filepath} skipped")
        # found a directory, so recursively traverse into
        # so that minification process can continue until done
        elif os.path.isdir(filepath):
            minify_files(filepath)


def main() -> None:
    """Perform the steps for the main function."""
    # parse the command-line arguments using argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--directory")
    parser.add_argument("-f", "--force", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    # create the argument parser
    args = parser.parse_args()
    # do not run the script unless quarto is rendering
    # all of the files (i.e., do not run during preview)
    if not os.getenv("QUARTO_PROJECT_RENDER_ALL") and not args.force:
        sys.exit()
    # define the default directory that will contain
    # the contents that are going to be minified
    directory_path = "_site"
    # there is a directory, so use it instead of
    # the default directory
    if args.directory is not None:
        directory_path = args.directory
    # perform the minification of all of the files
    # inside of the directory; note that this is
    # a destructive operation that changes the
    # contents of the specified directory
    minify_files(directory_path)


if __name__ == "__main__":
    # run the main function
    # that controls all of the parsing
    # of the bibliography entries
    main()
