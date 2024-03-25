import logging
from pathlib import Path
from time import sleep
from typing import Optional

from dotenv import load_dotenv

from src import ROOT_PATH
from src.benchmark.base_benchmark import BaseBenchmark
from src.manager.conversation_manager import ConversationManager
from src.preprocessing.process_notebook import string_to_notebook
from src.preprocessing.selenium_notebook import SeleniumNotebook

env = load_dotenv()
log = logging.getLogger(__name__)


class ErrorSolvingPipeline:
    @staticmethod
    def find_error(notebook: SeleniumNotebook, restart_kernel: bool = True) -> int | None:
        if restart_kernel:
            notebook.restart_kernel()

        success, error_cell_num = notebook.execute_all()
        return error_cell_num if not success else None

    @staticmethod
    def solve_error(
        step: int,
        error_cell_num: int,
        manager: ConversationManager,
        session_uuid: str = "",
        previous_output: Optional[str] = None,
    ):
        notebook: SeleniumNotebook = manager.environment

        if step == 0:
            error_trace = notebook.get_cell_output(notebook.cells[error_cell_num])
            if not error_trace:
                raise ValueError("Provided cell doesn't contain error output")

            notebook_source = str(notebook)

            agent_response = manager.interact(
                prompt="",
                session_uuid=session_uuid,
                first=True,
                notebook_source=notebook_source,
                error_trace=error_trace,
                cell_amount=len(notebook.cells),
                cell_num=error_cell_num,
            )

        else:
            agent_response = manager.interact(
                prompt=previous_output,
                session_uuid=session_uuid,
            )

        function_call = manager.parse_agent_response(agent_response)
        session_uuid = function_call.get("session_uuid")

        if function_call.get("tool") == "finish":
            return "[finish_function]", session_uuid

        error, env_response = manager.execute_tools(function_call)
        env_response = manager.parse_environment_response(env_response)
        output = manager.create_instruction(env_response)

        return output, session_uuid

    @staticmethod
    def check_solution(error_cell_num: int, notebook: SeleniumNotebook, restart_kernel: bool = False) -> bool:
        if restart_kernel:
            notebook.restart_kernel()

        error, _ = notebook.execute_cell(notebook.cells[error_cell_num])
        success = not error

        return success

    def run(self, manager: ConversationManager, max_iterations: int = 5, debug: bool = False) -> bool:
        step, output = 0, None

        if debug:
            input("PUSH TO CONTINUE")

        notebook: SeleniumNotebook = manager.environment
        error_cell_num = self.find_error(notebook, restart_kernel=True)
        if error_cell_num is None:
            return True

        if debug:
            input("PUSH TO CONTINUE")

        session_uuid = ""
        while step < max_iterations:
            log.info(f"[STEP] Step {step} started")
            output, session_uuid = self.solve_error(
                step=step,
                session_uuid=session_uuid,
                error_cell_num=error_cell_num,
                manager=manager,
                previous_output=output,
            )

            if debug:
                input("PUSH TO CONTINUE")

            if output == "[finish_function]":
                return self.check_solution(error_cell_num, notebook, restart_kernel=False)
            step += 1

        return False


class ErrorSolvingSingleNotebookBenchmark(BaseBenchmark):
    def evaluate(
        self,
        manager: ConversationManager,
        comment_finish: bool = True,
        save_solved: bool = True,
        save_name: str = "benchmark_ideformer",
        sleep_time: Optional[int] = 5,
        debug: bool = False,
        **kwargs,
    ) -> bool:
        selenium_notebook: SeleniumNotebook = manager.environment
        if selenium_notebook is None:
            raise ValueError("Notebook environment wasn't provided")

        pipeline, success = ErrorSolvingPipeline(), False
        with selenium_notebook as notebook:
            try:
                success = pipeline.run(manager, debug=debug)
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
                if debug:
                    input("PUSH TO CONTINUE")

                if comment_finish:
                    selenium_notebook.add_cell()
                    selenium_notebook.change_cell(-1, f"# {message}")

                if debug:
                    input("PUSH TO CONTINUE")

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
        manager: ConversationManager,
        notebook_path_list: Optional[tuple[Path, ...]] = None,
        notebook_environment_params: dict = None,
    ) -> float:
        if notebook_path_list is None:
            raise ValueError("No notebook has been provided")

        binary_benchmark = ErrorSolvingSingleNotebookBenchmark()
        results = []

        for notebook_path in notebook_path_list:
            # try:
            notebook = SeleniumNotebook(
                notebook_path=Path(notebook_path),
                **notebook_environment_params,
            )
            manager.init_environment(environment=notebook)
            success = binary_benchmark.evaluate(manager=manager)
            results.append(success)
            # except Exception as e:
            #     print(e)
            #     results.append(False)
            # finally:
            #     continue

        return sum(results) / len(results)
