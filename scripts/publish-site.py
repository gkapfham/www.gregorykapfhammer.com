"""Publish the site with support for pre-render, render, and post-render steps."""

import argparse

from rich.console import Console

console = Console()

DEFAULT_CONSOLE_STYLE = "bold blue"


def main() -> None:
    """Perform the steps for the main function."""
    # parse the command-line arguments using argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--stage")
    parser.add_argument("-f", "--force", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    # create the argument parser
    args = parser.parse_args()
    # extract the stage from the command-line arguments
    stage = args.stage
    console.print(f":clap: Performing the {stage} stage")


if __name__ == "__main__":
    # run the main function
    # that controls the calls to the
    # various scripts that perform the
    # following steps:
    # 1. pre-render
    # 2. render
    # 3. post-render
    main()
