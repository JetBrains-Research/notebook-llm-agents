from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Self

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

    def execute_cell(self, cell_num: int) -> Cell:
        pass

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
    ntb_path = Path(ROOT_PATH / "data/test_notebooks/test_notebook.ipynb")
    test_string, test_end = "print('hello world!')", f"\n{'='*10}\n"

    ntb = StringNotebook(ntb_path)
    print(ntb, end=test_end)

    ntb = ntb.add_cell(test_string)
    print(ntb, end=test_end)

    ntb = ntb.change_cell(0, test_string)
    print(ntb, end=test_end)
