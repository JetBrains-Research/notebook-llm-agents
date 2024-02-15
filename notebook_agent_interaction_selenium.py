import os
from pathlib import Path
from time import sleep

from dotenv import load_dotenv
from omegaconf import OmegaConf

from src.agents.agents import GrazieChatAgent
from src.preprocessing.notebook import StringNotebook
from src.preprocessing.process_notebook import string_to_notebook
from src.preprocessing.selenium_notebook import SeleniumNotebook

env = load_dotenv()

if __name__ == "__main__":
    prompt_config = OmegaConf.load("prompts/fix_error_prompt_datalore.yaml")
    agent = GrazieChatAgent(token=os.environ["GRAZIE_TOKEN"], prompt=prompt_config)

    # notebook_path = Path("data/processed_notebooks/test_selenium.ipynb")
    notebook_path = Path("data/test_notebooks/NameError_iterative_imputer.ipynb")

    notebook_server = Path("http://localhost:8888/")

    ntb = StringNotebook(notebook_path)
    success, n = ntb.execute_all()

    with SeleniumNotebook(
        driver_path=Path(os.environ["CHROMIUM_DRIVER_PATH"]),
        notebook_path=notebook_path,
        server=notebook_server,  # TODO: Add function for server initialization
    ) as ntb:
        step = 0
        while not success and step < 6:
            error, num = ntb.execute_all()
            print(error)
            if num is not None:
                print(ntb.get_cell_output(ntb.cells[num]))

            print(f"STEP is {step}")
            error_trace = ntb.get_cell_output(ntb.cells[num])
            print(error_trace)
            ntb_source = ntb.__str__()
            _ = agent.interact(
                notebook=ntb, notebook_source=ntb_source, error_trace=error_trace
            )
            step += 1
            success, n = ntb.execute_all()
        sleep(5)

        if success:
            string_to_notebook(
                ntb.__str__(),
                Path("data/processed_notebooks"),
                "solved_" + notebook_path.name,
            )
        print(ntb)
