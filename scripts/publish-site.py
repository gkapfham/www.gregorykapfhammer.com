"""Publish the site with support for pre-render, render, and post-render steps."""

import argparse
import subprocess
from typing import List

from rich.console import Console

console = Console()

DEFAULT_CONSOLE_STYLE = "bold blue"
INDENT = "  "


def display_output(output: List[str]) -> None:
    """Display the lines output with indentation."""
    # print each line with a tab indentation
    for line in output:
        console.print(INDENT + line)


def incremental_display_output(process) -> None:
    # print each line with an indentation as it appears
    for line in iter(process.stderr.readline, b""):
        console.print("  " + line.decode(), end="")
    # pass


def pre_render() -> None:
    """Perform the pre-render step(s)."""
    # call the shell script for parsing the bibliography;
    # capture the output so that it can be displayed
    result = subprocess.run(
        ["python", "scripts/parse-bibliography.py", "--force"],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    # split the output into lines
    result_lines = result.stdout.splitlines()
    # display the output with indentation
    display_output(result_lines)


def render() -> None:
    """Perform the render step."""
    # call the quarto render command
    subprocess.run(
        ["quarto", "render", "index.qmd"],
        check=True,
    )


def minify() -> None:
    """Perform the minify step."""
    # run the minification script; make
    # sure to use the poetry environment
    # as this is the one that contains the
    # Rust-based minifier that is not available
    # in nixpkgs and so not in the nix shell
    subprocess.run(
        ["poetry", "run", "python", "scripts/minify-files.py", "--verbose", "--force"],
        check=True,
    )


def main() -> None:
    """Perform the steps for the main function."""
    # parse the command-line arguments using argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--stage")
    # create the argument parser
    args = parser.parse_args()
    # extract the stage from the command-line arguments
    stage = args.stage
    # designate whether or not a prior stage was run
    prior_stage_ran = False
    # perform the pre-render step(s) if the stage is "pre-render" or "all"
    if stage in ("pre-render", "all"):
        current_stage = "pre-render"
        console.print(f":clap: Starting the '{current_stage}' stage")
        pre_render()
        console.print()
        console.print(f":clap: Finishing the '{current_stage}' stage")
        prior_stage_ran = True
    # perform the render step(s) if the stage is "render" or "all"
    if stage in ("render", "all"):
        current_stage = "render"
        if prior_stage_ran:
            console.print()
        console.print(f":clap: Starting the '{current_stage}' stage")
        console.print()
        render()
        console.print(f":clap: Finishing the '{current_stage}' stage")
        prior_stage_ran = True
    # perform the minify step(s) if the stage is "minify" or "all"
    if stage in ("minify", "all"):
        current_stage = "minify"
        if prior_stage_ran:
            console.print()
        console.print(f":clap: Starting the '{current_stage}' stage")
        console.print()
        minify()
        console.print()
        console.print(f":clap: Finishing the '{current_stage}' stage")
        prior_stage_ran = True


if __name__ == "__main__":
    # run the main function
    # that controls the calls to the
    # various scripts that perform the
    # following steps:
    # 1. pre-render
    # 2. render
    # 3. post-render
    main()
