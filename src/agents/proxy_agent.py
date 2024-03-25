import json
from typing import Any, Dict, Optional, Tuple

import requests
from grazie.api.client.profiles import LLMProfile, Profile

from src.agents.agents import BaseAgent


class ProxyAgent(BaseAgent):
    def __init__(
        self,
        token: str,
        url: str = "https://cloud-ideformer.labs.jb.gg/service/v5/ideformer",
        profile: LLMProfile = Profile.OPENAI_GPT_4,
        prompt_pattern: Optional[str] = None,
    ):
        self.profile = profile
        self.token = token
        self.url = url
        self.initial_prompt_pattern = prompt_pattern

    def _construct_request(self, prompt: str, session_uuid: str = "") -> Tuple[Dict[str, str], Dict[str, str]]:
        headers = {
            "Grazie-Authenticate-JWT": self.token,
            "Grazie-Agent": json.dumps({"name": "ideformer-proxy-app", "version": "1.0"}),
            "Content-Type": "application/json",
        }

        data = {
            "session_uuid": session_uuid,
            "api_content": {
                "agent_id": "notebook",
                "message": prompt,
                "config": {"profile": self.profile.name, "temperature": 1.0},
            },
        }
        body = {"data": json.dumps(data)}
        return headers, body

    def interact(self, prompt: str = "", **kwargs: Any) -> Dict:
        headers, body = self._construct_request(prompt, **kwargs)
        response = requests.post(self.url, headers=headers, json=body)
        print(response)
        return response.json()
