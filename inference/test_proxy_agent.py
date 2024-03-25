import json
import os

from dotenv import load_dotenv

from src import ROOT_PATH
from src.agents.proxy_agent import ProxyAgent

env = load_dotenv()


if __name__ == "__main__":
    with (ROOT_PATH / "prompts/example_prompt.txt").open("r") as f:
        prompt = f.read().replace("{", "{{").replace("}", "}}")  # Hack with Langchain

    agent = ProxyAgent(token=os.environ["GRAZIE_TOKEN"])
    response = agent.interact(prompt=prompt, session_uuid="").get("data")

    response = json.loads(response)
    session_uuid = response.get("session_uuid")
    print(response)

    response = agent.interact(prompt="error solved", session_uuid=session_uuid)
    print(response)
