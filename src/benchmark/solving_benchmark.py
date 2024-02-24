import logging
from pathlib import Path
from time import sleep
from typing import Optional

import nbformat
from dotenv import load_dotenv
from nbclient.exceptions import CellExecutionError
from nbconvert.preprocessors import ExecutePreprocessor

from src import ROOT_PATH
from src.agents.agents import BaseAgent, DummyAgent
from src.benchmark.base_benchmark import BaseBenchmark
from src.preprocessing.process_notebook import string_to_notebook
from src.preprocessing.selenium_notebook import SeleniumNotebook


env = load_dotenv()
log = logging.getLogger(__name__)


class ErrorSolvingPipeline:
    @staticmethod
    def find_error(
        notebook: SeleniumNotebook, restart_kernel: bool = True
    ) -> int | None:
        if restart_kernel:
            notebook.restart_kernel()

        success, error_cell_num = notebook.execute_all()
        return error_cell_num if not success else None

    @staticmethod
    def solve_error(
        step: int,
        error_cell_num: int,
        agent: BaseAgent,
        notebook: SeleniumNotebook,
        previous_output: Optional[str] = None,
    ):
        error_trace = notebook.get_cell_output(notebook.cells[error_cell_num])
        if not error_trace and step == 0:
            raise ValueError("Provided cell doesn't contain error output")

        notebook_source = str(notebook)
        interaction_output = agent.interact(
            notebook=notebook,
            output=previous_output,
            notebook_source=notebook_source,
            error_trace=error_trace,
            cell_amount=len(notebook.cells),
            cell_num=error_cell_num,
        )
        return interaction_output

    @staticmethod
    def check_solution(
        error_cell_num: int, notebook: SeleniumNotebook, restart_kernel: bool = False
    ) -> bool:
        if restart_kernel:
            notebook.restart_kernel()

        error, _ = notebook.execute_cell(notebook.cells[error_cell_num])
        success = not error
        return success

    def run(
        self, agent: BaseAgent, notebook: SeleniumNotebook, max_iterations: int = 5
    ) -> bool:
        step, output = 0, None
        error_cell_num = self.find_error(notebook, restart_kernel=True)
        if error_cell_num is None:
            return True

        while step < max_iterations:
            log.info(f"[STEP] Step {step} started")
            output = self.solve_error(step, error_cell_num, agent, notebook, output)

            if output == "[finish_function]":
                return self.check_solution(
                    error_cell_num, notebook, restart_kernel=False
                )
            step += 1

        return False


class ErrorSolvingSingleNotebookBenchmark(BaseBenchmark):
    def evaluate(
        self,
        agent: BaseAgent,
        selenium_notebook: SeleniumNotebook = None,
        comment_finish: bool = True,
        save_solved: bool = True,
        sleep_time: Optional[int] = 5,
        **kwargs,
    ) -> bool:
        if selenium_notebook is None:
            raise ValueError("Notebook environment wasn't provided")

        pipeline, success = ErrorSolvingPipeline(), False
        with selenium_notebook as notebook:
            try:
                success = pipeline.run(agent, notebook)
            finally:
                message = (
                    "[SOLVED] Error successfully solved".upper()
                    if success is True
                    else "[NOT SOLVED] Agent couldn't solve the error".upper()
                )
                log.info(message)

                if comment_finish:
                    notebook.add_cell()
                    notebook.change_cell(-1, f"# {message}")

                if success and save_solved:
                    # TODO: Think about remove from here
                    string_to_notebook(
                        str(notebook),
                        ROOT_PATH / "data/processed_notebooks",
                        "solved_" + notebook.notebook_path.name,
                    )

                sleep(sleep_time)

                return success


class ErrorSolvingBenchmark(BaseBenchmark):
    @staticmethod
    def run_notebook_locally(notebook_path: Path, overwrite: bool = False):
        nb_name = notebook_path.stem

        with notebook_path.open() as f:
            nb = nbformat.read(f, as_version=4)

        ep = ExecutePreprocessor(timeout=600, kernel_name="python3")
        exception_occurred: bool = False
        try:
            _ = ep.preprocess(nb, {"metadata": {"path": "/"}})
        except CellExecutionError:
            exception_occurred = True
        finally:
            if overwrite:
                with notebook_path.open(mode="wt") as f:
                    nbformat.write(nb, f)
            print(f"Completed execution of notebook {nb_name}")
            return exception_occurred, nb

    @staticmethod
    def run_notebook_docker():
        # TODO implement running the notebook in prepared docker container
        raise NotImplementedError()

    def evaluate(
        self, agent: BaseAgent, notebook_path_list: tuple[Path] = tuple()
    ) -> float:
        success = [
            self.run_notebook_locally(notebook_path)[0]
            for notebook_path in notebook_path_list
        ]
        return sum(success) / len(success)


if __name__ == "__main__":
    benchmark = ErrorSolvingBenchmark()
    agent = DummyAgent()

    ntb_paths = (ROOT_PATH / Path("data/test_notebooks/test_notebook_2.ipynb"),)
    result = benchmark.evaluate(agent, ntb_paths)
    print(result)
