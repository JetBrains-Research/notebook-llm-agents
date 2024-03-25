import os
from pathlib import Path

import docker
from omegaconf import OmegaConf

from src import ROOT_PATH
from src.agents.proxy_agent import ProxyAgent
from src.benchmark.solving_benchmark import ErrorSolvingSingleNotebookBenchmark
from src.manager.conversation_manager import ConversationManager
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


if __name__ == "__main__":
    benchmark = ErrorSolvingSingleNotebookBenchmark()

    experiment_config = OmegaConf.load(ROOT_PATH / "inference/single_notebook_interaction_config.yaml")
    docker_params = OmegaConf.to_container(experiment_config.docker_params)

    notebook_path = Path(experiment_config.notebook_params.notebook_path)
    notebook_server = Path(experiment_config.notebook_params.notebook_server)

    container = SafeDockerContainer(docker_params)
    with container:
        notebook = SeleniumNotebook(
            driver_path=Path(os.environ["CHROMIUM_DRIVER_PATH"]),
            notebook_path=notebook_path,
            server=notebook_server,
            headless=False,
        )
        prompt_pattern = OmegaConf.load("prompts/fix_error_prompt_custom.yaml").get("user_prompt")
        agent = ProxyAgent(token=os.environ["GRAZIE_TOKEN"], prompt_pattern=prompt_pattern)
        manager = ConversationManager(agent=agent, environment=notebook)

        result = benchmark.evaluate(manager, debug=False)
        print(result)
