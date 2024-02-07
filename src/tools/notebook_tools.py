from langchain.tools import BaseTool


class ExecuteCell(BaseTool):
    name: str = "Execute cell"
    description: str = "..."

    def _run(self):
        return NotImplementedError()


class ChangeCellSource(BaseTool):
    name: str = "Change cell source"
    description: str = "..."

    def _run(self):
        return NotImplementedError()


class GetPreviousExecutions(BaseTool):
    name: str = "Get previous executions"
    description: str = "..."

    def _run(self):
        return NotImplementedError()
