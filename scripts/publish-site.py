"""Publish the site with support for pre-render, render, and post-render steps."""

import argparse
import subprocess
from typing import Callable, List

from rich.console import Console

console = Console()

use_poetry_venv = False

INDENT = "  "


def display_output(output: List[str]) -> None:
    """Display the lines output with indentation."""
    # print each line with a tab indentation
    for line in output:
        console.print(INDENT + line)


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
    if use_poetry_venv:
        subprocess.run(
            [
                "poetry",
                "run",
                "python",
                "scripts/minify-files.py",
                "--verbose",
                "--force",
            ],
            check=True,
        )
    else:
        subprocess.run(
            ["python", "scripts/minify-files.py", "--verbose", "--force"],
            check=True,
        )


def perform_stage(stage: str, command: Callable) -> bool:
    """Perform the stage."""
    console.print(f":clap: Starting the '{stage}' stage")
    command()
    console.print()
    console.print(f":clap: Finishing the '{stage}' stage")
    prior_stage_ran = True
    return prior_stage_ran


def main() -> None:
    """Perform the steps for the main function."""
    global use_poetry_venv
    # parse the command-line arguments using argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--stage")
    parser.add_argument("-p", "--use-poetry-venv", action="store_true")
    # create the argument parser
    args = parser.parse_args()
    # extract the stage from the command-line arguments
    stage = args.stage
    use_poetry_venv = args.use_poetry_venv
    # designate whether or not a prior stage was run
    prior_stage_ran = False
    # PRE-RENDER: perform the pre-render step(s) if the stage is "pre-render" or "all"
    if stage in ("pre-render", "all"):
        if prior_stage_ran:
            console.print()
        current_stage = "pre-render"
        command = pre_render
        prior_stage_ran = perform_stage(current_stage, command)
    # RENDER: perform the render step(s) if the stage is "render" or "all"
    if stage in ("render", "all"):
        if prior_stage_ran:
            console.print()
        current_stage = "render"
        command = render
        prior_stage_ran = perform_stage(current_stage, command)
    # MINIFY: perform the minify step(s) if the stage is "minify" or "all"
    if stage in ("minify", "all"):
        if prior_stage_ran:
            console.print()
        current_stage = "minify"
        command = minify
        prior_stage_ran = perform_stage(current_stage, command)


if __name__ == "__main__":
    # run the main function
    # that controls the calls to the
    # various scripts that perform the
    # following steps:
    # 1. pre-render
    # 2. render
    # 3. post-render
    main()