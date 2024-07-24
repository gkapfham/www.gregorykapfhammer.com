"""Publish the site with support for pre-render, render, and post-render steps."""

import argparse
import subprocess

from rich.console import Console

console = Console()

DEFAULT_CONSOLE_STYLE = "bold blue"


def pre_render() -> None:
    """Perform the pre-render steps."""
    # subprocess.run(["python", "scripts/parse-bibliography.py", "--force"], check=True)
    # call the shell script for parsing the bibliography
    result = subprocess.run(
        ["python", "scripts/parse-bibliography.py", "--force"],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    # split the output into lines
    lines = result.stdout.splitlines()
    # print each line with a tab indentation
    for line in lines:
        print("  " + line)


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
    # perform the pre-render steps if the stage is "pre-render" or "all"
    if stage in ("pre-render", "all"):
        console.print(f":clap: Starting the '{stage}' stage")
        pre_render()
        console.print()
        console.print(f":clap: Finishing the '{stage}' stage")


if __name__ == "__main__":
    # run the main function
    # that controls the calls to the
    # various scripts that perform the
    # following steps:
    # 1. pre-render
    # 2. render
    # 3. post-render
    main()
