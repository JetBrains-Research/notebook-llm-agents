import os
from pathlib import Path

from single_notebook_interaction import init_agent, SafeDockerContainer
from src import ROOT_PATH
from src.benchmark.solving_benchmark import ErrorSolvingBenchmark

if __name__ == "__main__":
    notebook_environment_params = {
        "driver_path": Path(os.environ["CHROMIUM_DRIVER_PATH"]),
        "server": Path("http://localhost:8888/"),
        "headless": False,
    }

    docker_params = {
        "image": "agent-jupyter-interaction-docker-image",
        "ports": {"8888/tcp": 8888},
        "volumes": {ROOT_PATH / "data": {"bind": "/app/data", "mode": "rw"}},
        "detach": True,
    }

    notebook_path_list = tuple(Path("data/test_notebooks/").glob("*.ipynb"))[:3]

    benchmark = ErrorSolvingBenchmark()
    agent = init_agent()

    container = SafeDockerContainer(docker_params)
    with container:
        result = benchmark.evaluate(
            agent, notebook_path_list, notebook_environment_params
        )
        print(f"Totally solved {int(result * 100)}% of provided notebooks")
