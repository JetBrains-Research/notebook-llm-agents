import io
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Self

from tqdm import tqdm

from src import ROOT_PATH
from src.preprocessing.process_notebook import notebook_to_string


@dataclass
class Cell:
    cell_num: int
    cell_source: str
    cell_output: Optional[dict[str, str]] = None


class NotebookBase(ABC):
    @abstractmethod
    def execute_cell(self, **kwargs: Any) -> Cell:
        pass

    @abstractmethod
    def add_cell(self, cell_source: str) -> Self:
        pass

    @abstractmethod
    def change_cell(self, cell_num: int, new_cell_source: str) -> Self:
        pass

    def __getitem__(self, cell_num: int) -> Cell:
        pass


class StringNotebook(NotebookBase):
    def __init__(self, notebook_path: Path, sep: str = "\n#%% --\n"):
        self.notebook_path = notebook_path
        self.sep = sep
        self.cells = self._parse_notebook(notebook_path, sep)

    @staticmethod
    def _parse_notebook(notebook_path: Path, sep: str) -> list[Cell]:
        notebook_source = notebook_to_string(notebook_path, sep=sep)
        cells = [Cell(cell_num=num, cell_source=source) for num, source in enumerate(notebook_source.split(sep))]
        return cells

    def _prepare_source(self, execution_list: list[Cell]) -> str:
        return self.sep.join([cell.cell_source for cell in execution_list])

    def _prepare_execution_list(self, exclude_indices: Optional[list[int]] = None) -> list[Cell]:
        exclude_indices = exclude_indices if exclude_indices is not None else []
        return list(filter(lambda x: x.cell_num not in exclude_indices, self.cells))

    def execute_cell(self, execution_list: list[Cell]) -> Cell:
        code = self._prepare_source(execution_list)
        stdout, stderr = io.StringIO(), io.StringIO()

        prev_stdout, prev_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = stdout, stderr

        cell_output = {"text": None, "error": None}
        try:
            exec(code)
        except Exception as e:
            cell_output["error"] = e
        finally:
            cell = execution_list[-1]
            cell_output["text"] = stdout.getvalue()
            cell.cell_output = cell_output

            sys.stdout, sys.stderr = prev_stdout, prev_stderr
            stdout.close()
            stderr.close()

            return cell

    def execute_all(
        self, progress_bar: bool = True, exclude_indices: Optional[list[int]] = None
    ) -> tuple[bool, Optional[int]]:
        execution_list = self._prepare_execution_list(exclude_indices=exclude_indices)
        gen = enumerate(execution_list)
        gen = tqdm(gen) if progress_bar else gen

        for idx, _ in gen:
            cell_sequence = execution_list[: idx + 1]
            resulted_cell = self.execute_cell(cell_sequence)

            if resulted_cell.cell_output.get("error", None) is not None:
                print(f"Cell with num {idx} caused an error")
                return False, resulted_cell.cell_num
        return True, None

    def add_cell(self, cell_source: str) -> Self:
        new_cell = Cell(cell_num=len(self.cells), cell_source=cell_source)
        self.cells.append(new_cell)
        return self

    def change_cell(self, cell_num: int, new_cell_source: str) -> Self:
        cell = self.cells[cell_num]
        cell.cell_source = new_cell_source
        self.cells[cell.cell_num] = cell
        return self

    def __getitem__(self, cell_num: int) -> Cell:
        if cell_num >= len(self.cells):
            raise IndexError(f"Unexpected index number in list with size {len(self.cells)}")

        return self.cells[cell_num]

    def __str__(self):
        return self.sep.join([f"{cell.cell_source}" for cell in self.cells])


if __name__ == "__main__":
    ntb_path = Path(ROOT_PATH / "data/test_notebooks/test_notebook_2.ipynb")
    test_string, test_end, ex_ind = (
        "print('hello world!')",
        f"\n{'='*10}\n",
        [],
    )

    ntb = StringNotebook(ntb_path)
    print(ntb, end=test_end)

    res, n = ntb.execute_all()
    print(res, n)

    if n is not None:
        ex_ind.append(n)
        res, n = ntb.execute_all(exclude_indices=ex_ind)
        print(res, n)
