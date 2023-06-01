"""Copy files from a source directory to a destination directory."""

import shutil
from pathlib import Path


def copy_pdf_files(source_dir: str, destination_dir: str) -> None:
    """Copy files from the source directory to the destination directory."""
    # create pathlib Path objects out of the two directories
    source_path = Path(source_dir)
    destination_path = Path(destination_dir)
    # create the destination directory if it doesn't exist
    destination_path.mkdir(parents=True, exist_ok=True)
    # iterate over all files in the source directory
    for file_path in source_path.glob("*.pdf"):
        # construct the destination file path
        destination_file = destination_path / file_path.name
        # copy the file to the destination directory
        shutil.copy2(file_path, destination_file)


if __name__ == "__main__":
    copy_pdf_files("_resources/research/papers/key", "_site/research/papers/key")
