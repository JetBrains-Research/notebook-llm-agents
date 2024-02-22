import os
from pathlib import Path
from time import sleep

import docker
from dotenv import load_dotenv
from omegaconf import OmegaConf

from src.agents.agents import GrazieChatAgent
from src.preprocessing.process_notebook import string_to_notebook
from src.preprocessing.selenium_notebook import SeleniumNotebook

env = load_dotenv()

if __name__ == "__main__":
    prompt_config = OmegaConf.load("prompts/fix_error_prompt_datalore.yaml")
    agent = GrazieChatAgent(token=os.environ["GRAZIE_TOKEN"], prompt=prompt_config)

    client = docker.from_env()
    container = client.containers.run(
        "agent-jupyter-interaction-docker-image", ports={"8888/tcp": 8888}, detach=True
    )

    notebook_path = Path("test_notebooks/test_notebook.ipynb")
    notebook_server = Path("http://localhost:8888/")

    with SeleniumNotebook(
        driver_path=Path(os.environ["CHROMIUM_DRIVER_PATH"]),
        notebook_path=notebook_path,
        server=notebook_server,
        headless=True,
    ) as ntb:
        ntb.restart_kernel()
        step, success = 0, False
        while not success and step < 6:
            print(f"[START STEP] {step}")
            error, num = ntb.execute_all()
            if num is not None:
                print(ntb.get_cell_output(ntb.cells[num]))

            error_trace = ntb.get_cell_output(ntb.cells[num])
            ntb_source = ntb.__str__()

            _ = agent.interact(
                notebook=ntb,
                notebook_source=ntb_source,
                error_trace=error_trace,
                cell_number=len(ntb.cells),
            )
            step += 1
            success, n = ntb.execute_all()

        if success:
            print("[SOLVED] Error successfully solved")
            ntb.add_cell()
            ntb.change_cell(-1, "# ERROR SUCCESSFULLY SOLVED")
            string_to_notebook(
                ntb.__str__(),
                Path("data/processed_notebooks"),
                "solved_" + notebook_path.name,
            )

        sleep(5)

    container.stop()
    container.remove()
