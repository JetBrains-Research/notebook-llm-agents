import logging
from pathlib import Path
from time import sleep
from typing import Optional

from dotenv import load_dotenv

from src import ROOT_PATH
from src.agents.agents import BaseAgent
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
        save_name: str = "benchmark_datalore",
        sleep_time: Optional[int] = 5,
        **kwargs,
    ) -> bool:
        if selenium_notebook is None:
            raise ValueError("Notebook environment wasn't provided")

        pipeline, success = ErrorSolvingPipeline(), False
        with selenium_notebook as notebook:
            try:
                success = pipeline.run(agent, notebook)
            except Exception as e:
                print(e)
                logging.info(f"[INTERNAL_ERROR] {e}")
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
                    save_path = ROOT_PATH / "data/processed_notebooks" / save_name
                    if not save_path.exists():
                        save_path.mkdir(exist_ok=True)
                    string_to_notebook(
                        str(notebook),
                        save_path,
                        "solved_" + notebook.notebook_path.name,
                    )

                sleep(sleep_time)

                return success


class ErrorSolvingBenchmark(BaseBenchmark):
    def evaluate(
        self,
        agent: BaseAgent,
        notebook_path_list: Optional[tuple[Path]] = None,
        notebook_environment_params: dict = None,
    ) -> float:
        if notebook_path_list is None:
            raise ValueError("No notebook has been provided")

        binary_benchmark = ErrorSolvingSingleNotebookBenchmark()
        results = []

        for notebook_path in notebook_path_list:
            try:
                agent.init_chat()
                notebook = SeleniumNotebook(
                    notebook_path=notebook_path,
                    **notebook_environment_params,
                )
                success = binary_benchmark.evaluate(agent, notebook)
                results.append(success)
            except Exception as e:
                print(e)
                results.append(False)
            finally:
                continue

        return sum(results) / len(results)
