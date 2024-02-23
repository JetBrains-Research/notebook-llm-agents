import logging
import os
from pathlib import Path
from time import sleep

import docker
from dotenv import load_dotenv
from omegaconf import OmegaConf

from src.agents.agents import GrazieChatAgent
from src.preprocessing.process_notebook import string_to_notebook
from src.preprocessing.selenium_notebook import SeleniumNotebook
from src import ROOT_PATH

env = load_dotenv()
log = logging.getLogger(__name__)


if __name__ == "__main__":
    prompt_config = OmegaConf.load("prompts/fix_error_prompt_datalore.yaml")
    agent = GrazieChatAgent(token=os.environ["GRAZIE_TOKEN"], prompt=prompt_config)

    client = docker.from_env()
    container = client.containers.run(
        "agent-jupyter-interaction-docker-image",
        ports={"8888/tcp": 8888},
        volumes={ROOT_PATH / "data": {"bind": "/app/data", "mode": "rw"}},
        detach=True,
    )

    sleep(5)
    notebook_path = Path("data/test_notebooks/test_notebook.ipynb")
    notebook_server = Path("http://localhost:8888/")

    try:
        with SeleniumNotebook(
            driver_path=Path(os.environ["CHROMIUM_DRIVER_PATH"]),
            notebook_path=notebook_path,
            server=notebook_server,
            headless=False,
        ) as ntb:
            ntb.restart_kernel()
            (success, num), step = ntb.execute_all(), 0

            while not success and step < 6:
                error_trace = ntb.get_cell_output(ntb.cells[num])
                ntb_source = ntb.__str__()

                _ = agent.interact(
                    notebook=ntb,
                    notebook_source=ntb_source,
                    error_trace=error_trace,
                    cell_number=len(ntb.cells),
                )
                is_error, error_trace = ntb.execute_cell(ntb.cells[num])
                success = not is_error
                step += 1

            if success:
                log.info("[SOLVED] Error successfully solved".upper())
                ntb.add_cell()
                ntb.change_cell(-1, "# ERROR SUCCESSFULLY SOLVED")
                string_to_notebook(
                    ntb.__str__(),
                    Path("data/processed_notebooks"),
                    "solved_" + notebook_path.name,
                )
            sleep(5)

    except Exception as e:
        print(e)
    finally:
        container.stop()
        container.remove()
