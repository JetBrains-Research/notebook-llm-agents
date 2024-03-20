import json
from typing import Any, Dict, Tuple

import requests
from grazie.api.client.profiles import LLMProfile, Profile

from src.agents.agents import BaseAgent


class ProxyAgent(BaseAgent):
    def __init__(
        self,
        token: str,
        profile: LLMProfile = Profile.OPENAI_GPT_4,
    ):
        self.profile = profile
        self.token = token

    def _construct_request(self, prompt: str) -> Tuple[Dict[str, str], Dict[str, str]]:
        headers = {
            "Grazie-Authenticate-JWT": self.token,
            "Grazie-Agent": json.dumps({"name": "ideformer-proxy-app", "version": "1.0"}),
            "Content-Type": "application/json",
        }
        data = {
            "session_uuid": "",
            "api_content": {
                "agent_id": "notebook",
                "message": prompt,
                "config": {"profile": self.profile.name, "temperature": 1.0},
            },
        }
        body = {"data": json.dumps(data)}
        return headers, body

    def interact(self, prompt: str = "", **kwargs: Any) -> Dict:
        url = "https://cloud-ideformer.labs.jb.gg/service/v5/ideformer"
        headers, body = self._construct_request(prompt)
        response = requests.post(url, headers=headers, json=body)
        return response.json()
