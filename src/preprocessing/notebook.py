import io
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Self

from tqdm import tqdm

from src import ROOT_PATH
from src.preprocessing.process_notebook import notebook_to_string


@dataclass
class Cell:
    cell_num: int
    cell_source: str
    cell_output: Optional[str] = None


class NotebookBase(ABC):
    @abstractmethod
    def execute_cell(self, cell_num: int) -> Cell:
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
    def execute_cell(self, cell_num: int) -> Cell:
        pass

    def __init__(self, notebook_path: Path, sep: str = "\n#%% --\n"):
        self.notebook_path = notebook_path
        self.sep = sep
        self.cells = self._parse_notebook(notebook_path, sep)

    @staticmethod
    def _parse_notebook(notebook_path: Path, sep: str) -> list[Cell]:
        notebook_source = notebook_to_string(notebook_path, sep=sep)
        cells = [
            Cell(cell_num=num, cell_source=source)
            for num, source in enumerate(notebook_source.split(sep))
        ]
        return cells

    def _prepare_for_execution(self, cells: list[Cell]):
        source = self.sep.join([f"{cell.cell_source}" for cell in cells])
        return source

    def execute_cells(self, cells: list[Cell]) -> Cell:
        code = self._prepare_for_execution(cells)
        print(code)
        print("." * 20)
        stdout, stderr = io.StringIO(), io.StringIO()

        prev_stdout, prev_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = stdout, stderr

        cell_output = {"text": None, "error": None}
        try:
            exec(code)
        except:
            cell_output["error"] = True
        finally:
            cell = cells[-1]
            cell_output["text"] = stdout.getvalue()
            cell.cell_output = cell_output

            sys.stdout, sys.stderr = prev_stdout, prev_stderr
            stdout.close()
            stderr.close()

            return cell

    def execute_all(
        self, progress_bar: bool = True, exclude_nums: Optional[list[int]] = None
    ) -> tuple[bool, Optional[int]]:
        chosen_cells = (
            self.cells
            if exclude_nums is None
            else [obj for i, obj in enumerate(self.cells) if i not in exclude_nums]
        )

        gen = tqdm(enumerate(chosen_cells)) if progress_bar else enumerate(chosen_cells)
        for num, _ in gen:
            resulted_cell = self.execute_cells(chosen_cells[: num + 1])

            if resulted_cell.cell_output.get("error") is not None:
                print(f"Cell with num {num} caused an error")
                return False, num
        return True, None

    def add_cell(self, cell_source: str) -> Self:
        new_cell = Cell(cell_num=len(self.cells), cell_source=cell_source)
        self.cells.append(new_cell)
        return self

    def change_cell(self, cell_num: int, new_cell_source: str) -> Self:
        self.cells[cell_num] = Cell(cell_num=cell_num, cell_source=new_cell_source)
        return self

    def __getitem__(self, cell_num: int) -> Cell:
        if cell_num >= len(self.cells):
            raise IndexError(
                f"Unexpected index number in list with size {len(self.cells)}"
            )

        return self.cells[cell_num]

    def __str__(self):
        return self.sep.join([f"{cell.cell_source}" for cell in self.cells])


if __name__ == "__main__":
    ntb_path = Path(ROOT_PATH / "data/test_notebooks/test_notebook_2.ipynb")
    test_string, test_end = "print('hello world!')", f"\n{'='*10}\n"

    ntb = StringNotebook(ntb_path)
    print(ntb, end=test_end)

    res, n = ntb.execute_all()
    print(res, n)
    res, n = ntb.execute_all(exclude_nums=(n,))
    print(res, n)
