from langchain.tools import BaseTool
from src.preprocessing.notebook import NotebookBase, Cell


class ExecuteCell(BaseTool):
    name: str = "Execute cell"
    description: str = "..."

    def _run(self, notebook: NotebookBase, cell_num: int) -> Cell:
        _, output = notebook.execute_cell(notebook.cells[cell_num])
        return output


class ChangeCellSource(BaseTool):
    name: str = "Change cell source"
    description: str = "..."

    def _run(
        self, notebook: NotebookBase, cell_num: int, cell_source: str
    ) -> NotebookBase:
        notebook.change_cell(cell_num, cell_source)
        _, output = notebook.execute_cell(notebook.cells[cell_num])
        return output


class AddNewCell(BaseTool):
    name: str = "Add new cell"
    description: str = "..."

    def _run(self, notebook: NotebookBase, cell_source: str) -> NotebookBase:
        notebook.add_cell()
        notebook.change_cell(-1, cell_source)
        _, output = notebook.execute_cell(notebook.cells[-1])
        return notebook.add_cell(cell_source)


class GetPreviousExecutions(BaseTool):
    name: str = "Get previous executions"
    description: str = "..."

    def _run(self, notebook: NotebookBase):
        return NotImplementedError()
