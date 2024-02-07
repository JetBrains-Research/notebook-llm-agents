import os
from pathlib import Path

from dotenv import load_dotenv
from omegaconf import OmegaConf

from src.agents.agents import GrazieChatLlamaAgent, GrazieChatAgent
from src.preprocessing.process_notebook import notebook_to_string

env = load_dotenv()

if __name__ == "__main__":
    prompt_config = OmegaConf.load("prompts/generate_error_prompt.yaml")
    agent = GrazieChatAgent(token=os.environ["GRAZIE_TOKEN"], prompt=prompt_config)
    agent = GrazieChatLlamaAgent(token=os.environ["GRAZIE_TOKEN"], prompt=prompt_config)

    notebook_path = Path("data/test_notebooks/test_notebook.ipynb")
    notebook_source = notebook_to_string(notebook_path)

    error = "ValueError"
    response = agent.interact(notebook_source, error)
    print(response.content)
