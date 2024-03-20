import json
from typing import Dict

from omegaconf import DictConfig

from src.preprocessing.selenium_notebook import SeleniumNotebook


class NotebookTools:
    def __init__(self, notebook: SeleniumNotebook):
        self.notebook = notebook

    def create_cell(self, cell_source: str):
        self.notebook.add_cell()
        self.notebook.change_cell(-1, cell_source)

        last_cell = self.notebook.cells[-1]
        error, output = self.notebook.execute_cell(last_cell)
        return error, output

    def change_source(self, cell_num: int, cell_source: str):
        self.notebook.change_cell(cell_num, cell_source)

        cell = self.notebook.cells[cell_num]
        error, output = self.notebook.execute_cell(cell)
        return error, output

    def execute_cell(self, cell_number: int):
        cell = self.notebook.cells[cell_number]
        error, output = self.notebook.execute_cell(cell)
        return error, output


class Router:
    def __init__(self, agent, environment):
        self.agent = agent
        self.environment = environment
        self.tools = NotebookTools(environment)

    @staticmethod
    def parse_agent_response(agent_response):
        data = DictConfig(json.loads(agent_response["data"]))
        if not (function_call := data.api_content.api_name):
            return None

        args = data.api_content.args
        if "cell_num" in args:
            args.cell_num = int(args.cell_num)

        return {
            "tool": function_call,
            "args": args,
        }

    def execute_tools(self, instruction: Dict):
        tool, args = instruction["tool"], instruction["args"]
        environment_response = getattr(self.tools, tool)(**args)
        return environment_response

    @staticmethod
    def create_instruction(environment_response):
        return f"action executed with response {environment_response}"

    def pass_instruction_to_agent(self, instruction):
        self.agent.interact(instruction)

    def route(self, prompt: str):
        agent_response = self.agent.interact(prompt=prompt)

        iterations = 0
        agent_instruction = None
        while (agent_instruction is None) and iterations < 5:
            agent_response = self.agent.interact(prompt=prompt)
            agent_instruction = self.parse_agent_response(agent_response)
            iterations += 1

        print(agent_response)
        print(agent_instruction)
        if agent_instruction is None:
            raise Exception("Agent did not respond")
        elif agent_instruction["tool"] == "finish":
            return True

        environment_response = self.execute_tools(agent_instruction)
        env_instruction = self.create_instruction(environment_response)
        return env_instruction
