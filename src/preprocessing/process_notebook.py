import json
from pathlib import Path
from typing import Optional

import nbformat

from src import ROOT_PATH


def read_notebook(notebook_path: Path) -> dict:
    with open(notebook_path, "r") as f:
        source = f.read()
    notebook = nbformat.reads(source, as_version=nbformat.NO_CONVERT)
    return notebook


def notebook_to_string(
    notebook_path: Path,
    processed_folder_path: Optional[Path] = None,
    sep: str = "\n#%% --\n",
) -> str:
    notebook = read_notebook(notebook_path)
    notebook_string = sep.join(
        [cell.get("source") for cell in notebook.get("cells") if cell.get("cell_type") == "code"]
    )

    if processed_folder_path is not None:
        filename = notebook_path.name
        with open((processed_folder_path / filename).with_suffix(".md"), "w+") as f:
            f.write(notebook_string)

    return notebook_string


def string_to_notebook(
    markdown: Path | str,
    processed_folder_path: Optional[Path] = None,
    output_filename: Optional[str] = None,
    sep: str = "\n#%% --\n",
) -> dict:
    if isinstance(markdown, Path):
        with open(markdown, "r") as f:
            source = f.read()
    elif isinstance(markdown, str):
        source = markdown
    else:
        raise TypeError("Incorrect type for notebook string")

    notebook = {
        "cells": [{"cell_type": "code", "source": code} for code in source.split(sep)],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.7.1",
            },
        },
    }

    if processed_folder_path is not None:
        filename = (
            output_filename
            if output_filename is not None
            else "markdown.ipynb"
            if isinstance(markdown, str)
            else markdown.name
        )
        with open(processed_folder_path / filename, "w+") as f:
            json.dump(notebook, f)

    return notebook


if __name__ == "__main__":
    ntb_path = ROOT_PATH / "data/test_notebooks/test_notebook.ipynb"
    ntb = read_notebook(ntb_path)

    ntb_str = notebook_to_string(ntb_path, ROOT_PATH / "data/processed_notebooks")
    ntb_json = string_to_notebook(
        ntb_str,
        ROOT_PATH / "data/processed_notebooks",
        output_filename="test_notebook.ipynb",
    )
