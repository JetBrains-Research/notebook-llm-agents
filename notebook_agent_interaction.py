import os
from pathlib import Path

from dotenv import load_dotenv
from omegaconf import OmegaConf

from src.agents.agents import GrazieChatLlamaAgent, GrazieChatAgent
from src.preprocessing.notebook import StringNotebook
from src.preprocessing.process_notebook import notebook_to_string

env = load_dotenv()

if __name__ == "__main__":
    prompt_config = OmegaConf.load("prompts/fix_error_prompt_datalore.yaml")
    agent = GrazieChatAgent(token=os.environ["GRAZIE_TOKEN"], prompt=prompt_config)

    notebook_path = Path("data/test_notebooks/test_notebook_2.ipynb")
    ntb = StringNotebook(notebook_path)
    success, n = ntb.execute_all()

    step = 0
    while not success and step < 6:
        print(f"STEP is {step}")
        error_trace = ntb[n].cell_output.get("error")
        ntb_source = ntb.__str__()
        ntb = agent.interact(
            notebook=ntb, notebook_source=ntb_source, error_trace=error_trace
        )
        step += 1
        success, n = ntb.execute_all()
    print(ntb)
