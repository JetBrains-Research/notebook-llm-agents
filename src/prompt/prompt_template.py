from langchain_core.prompts import StringPromptTemplate
from langchain_core.tools import Tool


class CustomPromptTemplate(StringPromptTemplate):
    template: str
    tools: list[Tool]

    def format(self, **kwargs) -> str:
        raise NotImplementedError()
