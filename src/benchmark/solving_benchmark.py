from pathlib import Path

import nbformat
from nbclient.exceptions import CellExecutionError
from nbconvert.preprocessors import ExecutePreprocessor

from src import ROOT_PATH
from src.agents.agents import BaseAgent, DummyAgent
from src.benchmark.base_benchmark import BaseBenchmark


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
