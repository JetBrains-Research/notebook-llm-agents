import os
from pathlib import Path

from omegaconf import OmegaConf

from single_notebook_interaction import SafeDockerContainer
from src.preprocessing.selenium_notebook import SeleniumNotebook
from src.router.proxy_agent import ProxyAgent
from src.router.router import Router

if __name__ == "__main__":
    folder_path = Path("/Users/konstantingrotov/Documents/programming/projects/Data-Science-Hacks/")
    notebook_path_list = list((folder_path / "evaluation_sample_3").rglob("*.ipynb"))
    notebook_path_list = ["data" / el.relative_to(folder_path) for el in notebook_path_list]
    notebook_path_list = tuple([el for el in notebook_path_list if ".ipynb_checkpoints" not in str(el)][:])
    notebook_path = notebook_path_list[24]

    notebook_server = Path("http://localhost:2222/")

    docker_params = {
        "image": "agent-jupyter-interaction-docker-image",
        "ports": {"8888/tcp": 2222},
        "volumes": {folder_path: {"bind": "/app/data", "mode": "ro"}},
        "detach": True,
    }

    container = SafeDockerContainer(docker_params)
    with container:
        notebook = SeleniumNotebook(
            driver_path=Path(os.environ["CHROMIUM_DRIVER_PATH"]),
            notebook_path=notebook_path,
            server=notebook_server,
            headless=False,
        )

        with notebook as notebook:
            notebook.restart_kernel()
            success, error_cell_num = notebook.execute_all()
            if success:
                exit()

            error_trace = notebook.get_cell_output(notebook.cells[error_cell_num])
            notebook_source = str(notebook)

            prompt_config = OmegaConf.load("prompts/fix_error_prompt_custom.yaml")
            message = prompt_config.get("user_prompt").format(
                notebook_source=notebook_source,
                error_trace=error_trace,
                cell_amount=len(notebook.cells),
                cell_num=error_cell_num,
            )
            agent = ProxyAgent(token=os.environ["GRAZIE_TOKEN"], url="http://localhost:8000/request")
            router = Router(agent=agent, environment=notebook)

            while not success:
                env_response = router.route(prompt=message)
                print(env_response)
                if env_response is True:
                    print("FINISH")
                    success = True
                    break

                message = input("Print message to agent")
                if not message:
                    message = env_response
