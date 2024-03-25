import json
import logging
from copy import copy
from typing import Any

from grazie.api.client.chat.prompt import ChatPrompt
from grazie.api.client.endpoints import GrazieApiGatewayUrls
from grazie.api.client.gateway import AuthType, GrazieAgent, GrazieApiGatewayClient
from grazie.api.client.profiles import LLMProfile, Profile
from omegaconf import DictConfig

from src.agents.base_agent import BaseAgent
from src.preprocessing.notebook import NotebookBase
from src.tools import notebook_tools_grazie
from src.tools.notebook_tools import AddNewCell, ChangeCellSource, ExecuteCell

log = logging.getLogger(__name__)

AVAILABLE_MODELS: dict[str, LLMProfile] = {
    "llama_13b": Profile.GRAZIE_CHAT_LLAMA_V2_13b,
    "llama_7b": Profile.GRAZIE_CHAT_LLAMA_V2_7b,
    "gpt_3_5": Profile.OPENAI_CHAT_GPT,
    "gpt_4": Profile.OPENAI_GPT_4,
}


class GrazieChatAgent(BaseAgent):
    def __init__(
        self,
        token: str,
        prompt: DictConfig,
        profile: LLMProfile = AVAILABLE_MODELS["gpt_4"],
    ):
        self.client = GrazieApiGatewayClient(
            grazie_agent=GrazieAgent(name="grazie-api-gateway-client-readme", version="dev"),
            url=GrazieApiGatewayUrls.STAGING,
            auth_type=AuthType.SERVICE,
            grazie_jwt_token=token,
        )
        self.profile = profile
        self.prompt = prompt

        self.tools = {
            "change_cell": ChangeCellSource(),
            "execute_cell": ExecuteCell(),
            "add_cell": AddNewCell(),
        }
        self.chat = ChatPrompt().add_system(
            self.prompt.get("system_prompt") + "\nYOU MUST WRITE ONLY FUNCTION PARAMETERS"
        )
        self.error_cell_num = None

    def init_chat(self):
        prompt = self.prompt.get("system_prompt") + "\nYOU MUST WRITE ONLY FUNCTION PARAMETERS"
        self.chat = ChatPrompt().add_system(prompt)

    def interact(self, notebook: NotebookBase, output=None, **requests: Any):
        if output is not None:
            message = f"------\n Output is {output}\n------\n"
            self.chat = self.chat.add_user(message)

            log_message = message.replace("\n", "<line_sep>")
            logging.info(f"[CONTEXT] {log_message}")

        elif requests is not None:
            if "cell_num" in requests:
                self.error_cell_num = requests["cell_num"]

            message = self.prompt.get("user_prompt").format(**requests)
            self.chat = self.chat.add_user(message)

            log_message = message.replace("\n", "<line_sep>")
            logging.info(f"[CONTEXT] {log_message}")

        response = self.client.chat(
            chat=self.chat,
            profile=self.profile,
            parameters=notebook_tools_grazie,
        )

        params = json.loads(response.content)

        # Logging function call and its parameters
        params_log = copy(params)
        params_log["function_name"] = response.function_call
        log.info(f"[FUNC] {params_log}")

        if True:
            input("PUSH TO CONTINUE")

        if response.function_call == "finish":
            return "[finish_function]"

        if response.function_call is not None:
            self.chat.add_assistant_function(response.function_call, response.content)

        output = self.tools[response.function_call]._run(notebook=notebook, **params)

        return output
