import os
from pathlib import Path

from dotenv import load_dotenv
from omegaconf import OmegaConf

from src.agents.agents import GrazieChatAgent
from src.preprocessing.notebook import StringNotebook
from src.preprocessing.process_notebook import string_to_notebook

env = load_dotenv()

if __name__ == "__main__":
    prompt_config = OmegaConf.load("prompts/fix_error_prompt_datalore.yaml")
    agent = GrazieChatAgent(token=os.environ["GRAZIE_TOKEN"], prompt=prompt_config)

    notebook_path = Path("data/test_notebooks/NameError_iterative_imputer.ipynb")
    ntb = StringNotebook(notebook_path)
    success, n = ntb.execute_all()

    step = 0
    while not success and step < 6:
        print(f"STEP is {step}")
        error_trace = ntb[n].cell_output.get("error")
        print(error_trace)
        ntb_source = ntb.__str__()
        ntb = agent.interact(notebook=ntb, notebook_source=ntb_source, error_trace=error_trace)
        step += 1
        success, n = ntb.execute_all()

    string_to_notebook(ntb.__str__(), Path("data/processed_notebooks"), notebook_path.name)
    print(ntb)
