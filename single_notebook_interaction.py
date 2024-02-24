import os
from pathlib import Path

import docker
from omegaconf import OmegaConf

from src import ROOT_PATH
from src.agents.agents import GrazieChatAgent, BaseAgent
from src.benchmark.solving_benchmark import ErrorSolvingSingleNotebookBenchmark
from src.preprocessing.selenium_notebook import SeleniumNotebook


class SafeDockerContainer:
    def __init__(self, params: dict):
        self.params = params
        self.client = None
        self.container = None

    def __enter__(self):
        self.client = docker.from_env()
        self.container = self.client.containers.run(**self.params)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.container.stop()
        self.container.remove()


def init_agent() -> BaseAgent:
    prompt_config = OmegaConf.load("prompts/fix_error_prompt_custom.yaml")
    agent = GrazieChatAgent(token=os.environ["GRAZIE_TOKEN"], prompt=prompt_config)
    return agent


if __name__ == "__main__":
    benchmark = ErrorSolvingSingleNotebookBenchmark()
    notebook_path = Path("data/test_notebooks/NameError_list_of_lists_to_list.ipynb")
    notebook_server = Path("http://localhost:8888/")

    docker_params = {
        "image": "agent-jupyter-interaction-docker-image",
        "ports": {"8888/tcp": 8888},
        "volumes": {ROOT_PATH / "data": {"bind": "/app/data", "mode": "rw"}},
        "detach": True,
    }

    agent = init_agent()
    container = SafeDockerContainer(docker_params)
    with container:
        notebook = SeleniumNotebook(
            driver_path=Path(os.environ["CHROMIUM_DRIVER_PATH"]),
            notebook_path=notebook_path,
            server=notebook_server,
            headless=False,
        )
        result = benchmark.evaluate(agent, notebook)
        print(result)
