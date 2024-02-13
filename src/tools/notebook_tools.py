from langchain.tools import BaseTool
from src.preprocessing.notebook import NotebookBase, Cell


class ExecuteCell(BaseTool):
    name: str = "Execute cell"
    description: str = "..."

    def _run(self, notebook: NotebookBase, cell_num: int) -> Cell:
        return notebook.execute_cell(cell_num)


class ChangeCellSource(BaseTool):
    name: str = "Change cell source"
    description: str = "..."

    def _run(
        self, notebook: NotebookBase, cell_num: int, cell_source: str
    ) -> NotebookBase:

        return notebook.change_cell(cell_num, cell_source)


class AddNewCell(BaseTool):
    name: str = "Add new cell"
    description: str = "..."

    def _run(self, notebook: NotebookBase, cell_source: str) -> NotebookBase:
        return notebook.add_cell(cell_source)


class GetPreviousExecutions(BaseTool):
    name: str = "Get previous executions"
    description: str = "..."

    def _run(self, notebook: NotebookBase):
        return NotImplementedError()
