"""Publish the site with support for pre-render, render, and post-render steps."""

import argparse
import subprocess
from typing import Callable

from rich.console import Console

console = Console()

use_poetry_venv = False
render_file = None
host = "quarto-pub"

INDENT = "  "


def pre_render() -> None:
    """Perform the pre-render step(s)."""
    # call the shell script for parsing the bibliography;
    # capture the output so that it can be displayed
    python_script = "python scripts/parse-bibliography.py --force"
    run_python_script(python_script, use_poetry_venv)


def minify() -> None:
    """Perform the minify step."""
    # call the Python script for minifying the files
    python_script = "python scripts/minify-files.py --verbose --force"
    run_python_script(python_script, use_poetry_venv)


def copy() -> None:
    """Perform the copy files step."""
    # call the Python script for copying files;
    # by default this moves the PDFs to _site/
    python_script = "python scripts/copy-files.py --force"
    run_python_script(python_script, use_poetry_venv)


def run_python_script(script_path: str, use_poetry_venv: bool) -> None:
    """Call the Python script with or without the poetry venv."""
    # break the string into an array of strings
    script_path_parts = script_path.split()
    # run the command inside of a poetry venv
    if use_poetry_venv:
        subprocess.run(
            ["poetry", "run", *script_path_parts],
            check=True,
        )
    # run the command in the standard environment
    else:
        subprocess.run(
            script_path_parts,
            check=True,
        )


def render() -> None:
    """Perform the render step."""
    # call the quarto render command
    if render_file is None:
        subprocess.run(
            ["quarto", "render"],
            check=True,
        )
    else:
        subprocess.run(
            ["quarto", "render", render_file],
            check=True,
        )


def quarto() -> None:
    """Perform the step that publishes to Quarto-Pub or Netlify based on host."""
    # call the quarto render command
    quarto_publish_command = f"quarto publish {host} --no-render --no-prompt --no-browser"
    quarto_publish_command_parts = quarto_publish_command.split()
    subprocess.run(
        quarto_publish_command_parts,
        check=True,
    )


def perform_stage(command: Callable) -> bool:
    """Perform the stage."""
    stage = command.__name__
    console.print(f":clap: Starting the '{stage}' stage")
    command()
    console.print()
    console.print(f":clap: Finishing the '{stage}' stage")
    prior_stage_ran = True
    return prior_stage_ran


def main() -> None:  # noqa: PLR0912, PLR0915
    """Perform the steps for the main function."""
    global use_poetry_venv  # noqa: PLW0603
    global render_file  # noqa: PLW0603
    global host  # noqa: PLW0603
    # parse the command-line arguments using argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--use-poetry-venv", action="store_true")
    parser.add_argument("-r", "--render-file")
    parser.add_argument("-s", "--stages", nargs="+", default=[])
    # create the argument parser
    args = parser.parse_args()
    # extract the values from the command-line arguments;
    # note that stages is a list of strings that will be
    # empty if no stages are specified on the command-line
    stages = args.stages
    use_poetry_venv = args.use_poetry_venv
    render_file = args.render_file
    # designate whether or not a prior stage was run
    prior_stage_ran = False
    for stage in stages:
        # PRE-RENDER: perform the pre-render step(s) if the stage is "pre-render" or "all"
        if stage in ("pre-render", "all"):
            if prior_stage_ran:
                console.print()
            command = pre_render
            prior_stage_ran = perform_stage(command)
        # RENDER: perform the render step(s) if the stage is "render" or "all"
        if stage in ("render", "all"):
            if prior_stage_ran:
                console.print()
            command = render
            prior_stage_ran = perform_stage(command)
        # MINIFY: perform the minify step(s) if the stage is
        # "minify" or "post-render" or "all"
        if stage in ("minify", "post-render", "all"):
            if prior_stage_ran:
                console.print()
            command = minify
            prior_stage_ran = perform_stage(command)
        # COPY: perform the copy step(s) if the stage is
        # "copy" or "post-render" or "all"
        if stage in ("copy", "post-render", "all"):
            if prior_stage_ran:
                console.print()
            command = copy
            prior_stage_ran = perform_stage(command)
        # Quarto-Pub: perform the publish step(s) if the stage is
        # "quarto-pub" or "publish" or "all"
        if stage in ("quarto-pub", "publish"):
            # correct set the host to always use quarto-pub
            if stage == "publish":
                host = "quarto-pub"
            else:
                host = stage
            if prior_stage_ran:
                console.print()
            command = quarto
            prior_stage_ran = perform_stage(command)
        # Netlify: perform the publish step(s) if the stage is
        # "netlify" or "publish" or "all"
        if stage in ("netlify", "publish"):
            # correct set the host to always use netlify
            if stage == "publish":
                host = "netlify"
            else:
                host = stage
            if prior_stage_ran:
                console.print()
            command = quarto
            prior_stage_ran = perform_stage(command)


if __name__ == "__main__":
    # run the main function
    # that controls the calls to the
    # various scripts that perform the
    # following steps:
    # 1. pre-render
    # 2. render
    # 3. post-render
    # 3a. minify
    # 3b. copy
    # 4. publish
    # 4a. quarto-pub
    # 4b. netlify
    main()
