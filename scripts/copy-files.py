"""Copy files from a source directory to a destination directory."""

import argparse
import itertools
import os
import shutil
import sys
from pathlib import Path

from rich.console import Console

DEFAULT_GLOB = "*.pdf"

DEFAULT_SOURCE_DIRECTORY_PAPERS = "_resources/download/research/papers/key"
DEFAULT_DESTINATION_DIRECTORY_PAPERS = "_site/download/research/papers/key"

DEFAULT_SOURCE_DIRECTORY_PRESENTATIONS = "_resources/download/research/presentations/key"
DEFAULT_DESTINATION_DIRECTORY_PRESENTATIONS = "_site/download/research/presentations/key"

DEFAULT_SOURCE_DIRECTORIES = [
    DEFAULT_SOURCE_DIRECTORY_PAPERS,
    DEFAULT_SOURCE_DIRECTORY_PRESENTATIONS,
]
DEFAULT_DESTINATION_DIRECTORIES = [
    DEFAULT_DESTINATION_DIRECTORY_PAPERS,
    DEFAULT_DESTINATION_DIRECTORY_PRESENTATIONS,
]

DEFAULT_CONSOLE_STYLE = "bold blue"

console = Console()


def copy_files(
    source_dir: str, destination_dir: str, file_glob: str = DEFAULT_GLOB
) -> None:
    """Copy files from the source directory to the destination directory."""
    # create pathlib Path objects out of the two directories
    source_path = Path(source_dir)
    destination_path = Path(destination_dir)
    # create the destination directory if it doesn't exist
    destination_path.mkdir(parents=True, exist_ok=True)
    # iterate over all files in the source directory
    source_path_glob_iterator = source_path.glob(file_glob)
    # keep track of the number of files copied
    file_count = 0
    for file_path in source_path_glob_iterator:
        # construct the destination file path
        destination_file = destination_path / file_path.name
        # copy the file to the destination directory
        shutil.copy2(file_path, destination_file)
        # increment the file counter
        file_count = file_count + 1
    # output some debugging information about the completed copy
    console.print(
        f":tada: Finished copying {file_count} files", style=DEFAULT_CONSOLE_STYLE
    )


def main() -> None:
    """Perform the steps for the main function."""
    # parse the command-line arguments using argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source")
    parser.add_argument("-d", "--destination")
    parser.add_argument("-f", "--force", action="store_true")
    args = parser.parse_args()
    # do not run the script unless quarto is rendering
    # all of the files (i.e., do not run during preview)
    if not os.getenv("QUARTO_PROJECT_RENDER_ALL") and not args.force:
        sys.exit()
    # perform the default copies when there is no source and destination
    if args.source is None and args.destination is None:
        console.print(
            ":tada: Perform default copies since there were no parameters\n",
            style=DEFAULT_CONSOLE_STYLE,
        )
        # iterate through all of the default source and destination
        # directories in a lockstep fashion and perform copies
        for source_directory_current, destination_directory_current in zip(
            DEFAULT_SOURCE_DIRECTORIES, DEFAULT_DESTINATION_DIRECTORIES
        ):
            # determine the valid directory for the source
            source_directory = source_directory_current
            # use the current source directory
            console.print(
                f":clap: Using the source directory of {source_directory}\n",
                style=DEFAULT_CONSOLE_STYLE,
            )
            # use the valid destination directory
            destination_directory = destination_directory_current
            console.print(
                f":clap: Using the destination directory of {destination_directory}\n",
                style=DEFAULT_CONSOLE_STYLE,
            )
            # perform the copy from the source to the desination
            copy_files(source_directory, destination_directory)
    elif args.source is not None and args.destination is not None:
        source_directory = args.source
        destination_directory = args.destination
        # use the current source directory
        console.print(
            f":clap: Using the source directory of {source_directory}\n",
            style=DEFAULT_CONSOLE_STYLE,
        )
        # use the valid destination directory
        destination_directory = destination_directory_current
        console.print(
            f":clap: Using the destination directory of {destination_directory}\n",
            style=DEFAULT_CONSOLE_STYLE,
        )
        # perform the copy from the source to the desination
        copy_files(source_directory, destination_directory)
    else:
        console.print(
            "\n:wink: Could not perform copy due to invalid arguments\n",
            style=DEFAULT_CONSOLE_STYLE,
        )


if __name__ == "__main__":
    # run the main function
    # that controls all of the file copies
    main()
