import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from grazie.api.client.chat.prompt import ChatPrompt
from grazie.api.client.endpoints import GrazieApiGatewayUrls
from grazie.api.client.gateway import GrazieApiGatewayClient, AuthType, GrazieAgent
from grazie.api.client.llm_functions import FunctionDefinition
from grazie.api.client.llm_parameters import LLMParameters
from grazie.api.client.parameters import Parameters
from grazie.api.client.profiles import Profile, LLMProfile
from omegaconf import DictConfig, OmegaConf

from src import ROOT_PATH
from src.preprocessing.notebook import NotebookBase
from src.tools.notebook_tools import ChangeCellSource, AddNewCell, ExecuteCell

log = logging.getLogger(__name__)

AVAILABLE_MODELS: dict[str, LLMProfile] = {
    "llama_13b": Profile.GRAZIE_CHAT_LLAMA_V2_13b,
    "llama_7b": Profile.GRAZIE_CHAT_LLAMA_V2_7b,
    "gpt_3_5": Profile.OPENAI_CHAT_GPT,
    "gpt_4": Profile.OPENAI_GPT_4,
}


class BaseAgent(ABC):
    @abstractmethod
    def interact(self, **requests: Any) -> str:
        pass


class DummyAgent(BaseAgent):
    def interact(self) -> str:
        return "hi"


function_params = {
    LLMParameters.Functions: Parameters.JsonValue.from_functions(
        FunctionDefinition(
            name="change_cell",
            description="Change source of the existing cell in the notebook and execute it, returns the output of the cell",
        )
        .add_argument(
            name="cell_num",
            description="Number of the cell in the notebook (starting from 0).",
            _type=FunctionDefinition.FunctionParameterTypes.INTEGER,
            required=True,
        )
        .add_argument(
            name="cell_source",
            description="New source of the cell which should be changed",
            _type=FunctionDefinition.FunctionParameterTypes.STRING,
            required=True,
        ),
        FunctionDefinition(
            name="execute_cell",
            description="Executing cell in the notebook without changing its code, returns the output of the cell ",
        ).add_argument(
            name="cell_num",
            description="Number of the cell in the notebook (starting from 0).",
            _type=FunctionDefinition.FunctionParameterTypes.INTEGER,
            required=True,
        ),
        FunctionDefinition(
            name="add_cell",
            description="Append new cell in the notebook and execute it, returns the output of the cell ",
        )
        .add_argument(
            name="cell_num",
            description="Number of the cell in the notebook (starting from 0).",
            _type=FunctionDefinition.FunctionParameterTypes.INTEGER,
            required=True,
        )
        .add_argument(
            name="cell_source",
            description="New source of the cell which should be changed",
            _type=FunctionDefinition.FunctionParameterTypes.STRING,
            required=True,
        ),
    ),
}


class GrazieChatAgent(BaseAgent):
    def __init__(
        self,
        token: str,
        prompt: DictConfig,
        profile: LLMProfile = AVAILABLE_MODELS["gpt_4"],
    ):
        self.client = GrazieApiGatewayClient(
            grazie_agent=GrazieAgent(
                name="grazie-api-gateway-client-readme", version="dev"
            ),
            url=GrazieApiGatewayUrls.STAGING,
            auth_type=AuthType.USER,
            grazie_jwt_token=token,
        )
        self.profile = profile
        self.prompt = prompt

        self.tools = {
            "change_cell": ChangeCellSource(),
            "execute_cell": ExecuteCell(),
            "add_cell": AddNewCell(),
        }

    def interact(self, notebook: NotebookBase, **requests: Any) -> NotebookBase:
        response = self.client.chat(
            chat=ChatPrompt()
            .add_system(
                self.prompt.get("system_prompt")
                + "\nYOU MUST WRITE ONLY FUNCTION PARAMETERS"
            )
            .add_user(self.prompt.get("user_prompt").format(**requests)),
            profile=self.profile,
            parameters=function_params,
        )
        params = json.loads(response.content)
        log.info(f"[FUNC] {response.function_call}")
        log.info(f"[FUNC PARAMS] {params}")

        notebook = self.tools[response.function_call]._run(notebook=notebook, **params)
        return notebook


class GrazieChatLlamaAgent(GrazieChatAgent):
    def __init__(
        self,
        token: str,
        prompt: DictConfig,
        profile: LLMProfile = AVAILABLE_MODELS["llama_7b"],
    ):
        super().__init__(token, prompt, profile=profile)
        self.prompt = self.preprocess_user_prompt(self.prompt)

    @staticmethod
    def preprocess_user_prompt(prompt: DictConfig) -> DictConfig:
        llama_template = OmegaConf.load(ROOT_PATH / "prompts/templates/llama.yaml")
        prompt["user_prompt"] = llama_template["prompt_template"].format(
            system=prompt["system_prompt"], user=prompt["user_prompt"]
        )
        return prompt
