import json
import re
from collections import defaultdict
from typing import Dict, Optional

from omegaconf import DictConfig

from src.preprocessing.selenium_notebook import SeleniumNotebook
from src.tools.notebook_tools import NotebookTools


class ConversationManager:
    def __init__(self, agent, environment: Optional[SeleniumNotebook] = None):
        self.agent = agent
        self.init_environment(environment)
        self.conversations = defaultdict(lambda: 1)

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conversations = defaultdict(lambda: 1)

    def init_environment(self, environment: SeleniumNotebook):
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
            "session_uuid": data.session_uuid,
            "tool": function_call,
            "args": args,
        }

    @staticmethod
    def parse_environment_response(message: str):
        # message = "<LINE_SEP>".join(message.splitlines())
        message = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", message)
        env_response = message.replace("{", "{{").replace("}", "}}")
        return env_response

    def execute_tools(self, instruction: Dict):
        tool, args = instruction["tool"], instruction["args"]
        environment_response = getattr(self.tools, tool)(**args)
        return environment_response

    @staticmethod
    def create_instruction(environment_response):
        return f"Action executed with response {str(environment_response)}"

    def pass_instruction_to_agent(self, prompt: str, session_uuid: str = "") -> Dict:
        agent_response = self.agent.interact(prompt=prompt, session_uuid=session_uuid)
        return agent_response

    def interact(self, prompt: str, session_uuid: str = "", **kwargs):
        if session_uuid != "":
            self.conversations[session_uuid] += 1

        if kwargs.get("first"):
            kwargs.pop("first")
            prompt = self.agent.initial_prompt_pattern.format(**kwargs)
            prompt = self.parse_environment_response(prompt)

        agent_response = self.pass_instruction_to_agent(prompt=prompt, session_uuid=session_uuid)
        return agent_response

    def iterate(self, prompt: str, session_uuid: str = "", **kwargs):
        iterations, agent_instruction = 0, None

        while (agent_instruction is None) and iterations < 5:
            agent_response = self.pass_instruction_to_agent(prompt=prompt, session_uuid=session_uuid, **kwargs)
            agent_instruction = self.parse_agent_response(agent_response)
            iterations += 1

        if agent_instruction is None:
            raise Exception("Agent did not respond")
        elif agent_instruction["tool"] == "finish":
            return True

        return agent_instruction
