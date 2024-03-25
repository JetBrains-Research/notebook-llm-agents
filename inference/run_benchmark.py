import os
from pathlib import Path

from omegaconf import OmegaConf
from single_notebook_interaction import SafeDockerContainer

from src import ROOT_PATH
from src.agents.proxy_agent import ProxyAgent
from src.benchmark.solving_benchmark import ErrorSolvingBenchmark
from src.manager.conversation_manager import ConversationManager

if __name__ == "__main__":
    experiment_config = OmegaConf.load(ROOT_PATH / "inference/benchmark_config.yaml")

    notebook_environment_params = OmegaConf.to_container(experiment_config.notebook_params)
    notebook_environment_params = {
        key: Path(value) for key, value in notebook_environment_params.items() if isinstance(value, str)
    }

    docker_params = OmegaConf.to_container(experiment_config.docker_params)

    folder_path = Path(
        "/Users/konstantingrotov/Documents/programming/projects/Data-Science-Hacks/evaluation_sample_3/evaluation_sample/"
    )
    notebook_path_list = list(folder_path.rglob("*.ipynb"))
    notebook_path_list = [
        "data/evaluation_sample_3/evaluation_sample" / el.relative_to(folder_path) for el in notebook_path_list
    ]
    notebook_path_list = tuple([el for el in notebook_path_list if ".ipynb_checkpoints" not in str(el)][:2])
    benchmark = ErrorSolvingBenchmark()

    prompt_pattern = OmegaConf.load("prompts/fix_error_prompt_custom.yaml").get("user_prompt")
    agent = ProxyAgent(token=os.environ["GRAZIE_TOKEN"], prompt_pattern=prompt_pattern)
    manager = ConversationManager(agent=agent)

    container = SafeDockerContainer(docker_params)
    with container:
        result = benchmark.evaluate(
            manager=manager,
            notebook_path_list=notebook_path_list,
            notebook_environment_params=notebook_environment_params,
        )
        print(f"Totally solved {int(result * 100)}% of provided notebooks")
