from abc import ABC, abstractmethod
from typing import Any

from grazie.api.client.chat.prompt import ChatPrompt
from grazie.api.client.endpoints import GrazieApiGatewayUrls
from grazie.api.client.gateway import GrazieApiGatewayClient, AuthType, GrazieAgent
from grazie.api.client.profiles import Profile, LLMProfile
from omegaconf import DictConfig, OmegaConf

from src import ROOT_PATH

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


class GrazieChatAgent(BaseAgent):
    def __init__(
        self,
        token: str,
        prompt: DictConfig,
        profile: LLMProfile = AVAILABLE_MODELS["gpt_3_5"],
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

    def interact(self, *requests: Any) -> str:
        response = self.client.chat(
            chat=ChatPrompt()
            .add_system(self.prompt.get("system_prompt"))
            .add_user(self.prompt.get("user_prompt").format(*requests)),
            profile=self.profile,
        )
        return response.content


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
