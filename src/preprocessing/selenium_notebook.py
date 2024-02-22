from pathlib import Path
from time import sleep
from typing import Optional

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

from src.preprocessing import (
    PROGRESS_EXECUTION_ELEMENT,
    INSERT_CELL_BELOW_ELEMENT,
    LAST_CELL_ELEMENT,
    CELL_EDIT_AREA,
    CELL_OUTPUT_AREA,
    CELL_ELEMENT,
)
from src.preprocessing.notebook import NotebookBase


class SeleniumNotebook(NotebookBase):
    def __init__(
        self,
        notebook_path: Path,
        driver_path: Path,
        server: Path,
        sep: str = "\n#%% --\n",
        headless: bool = False,
    ):
        self.notebook_path = notebook_path
        self.driver_path = driver_path
        self.server = server
        self.sep = sep
        self.headless = headless

        self.driver = None

    def __enter__(self, sleep_time: float = 5.0):
        service, options = (
            Service(executable_path=str(self.driver_path)),
            webdriver.ChromeOptions(),
        )
        if self.headless:
            options.add_argument("headless")
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.get(str(self.server / "notebooks/" / self.notebook_path))
        sleep(sleep_time)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()

    @property
    def cells(self):
        return self.driver.find_elements(By.XPATH, CELL_ELEMENT)

    @staticmethod
    def get_cell_output(cell: WebElement):
        output = ""
        try:
            cell_outputs = cell.find_elements(By.XPATH, CELL_OUTPUT_AREA)
            output = "".join([output.text for output in cell_outputs])
        except Exception as e:
            print("Error while printing cell output:", str(e))
        finally:
            return output

    @staticmethod
    def _wait_for_execution(cell: WebElement, waiting_time_delta: float = 0.1):
        wait_time = 0
        while True:
            try:
                cell.find_element(
                    By.XPATH,
                    PROGRESS_EXECUTION_ELEMENT,
                )
                sleep(waiting_time_delta)
                wait_time += waiting_time_delta
            except NoSuchElementException:
                break

    def execute_cell(self, cell: WebElement):
        traceback_message = "Traceback (most recent call last)"
        cell.click()
        action = ActionChains(self.driver).key_down(Keys.COMMAND).key_down(Keys.ENTER)
        action.perform()
        self._wait_for_execution(cell)

        output = self.get_cell_output(cell)
        error = True if traceback_message in output else False
        return error, output

    def add_cell(
        self, current_cell: Optional[WebElement] = None, sleep_time: float = 0.5
    ):
        cell = (
            current_cell
            if current_cell is not None
            else self.driver.find_element(By.XPATH, LAST_CELL_ELEMENT)
        )
        cell.click()
        self.driver.find_element(By.XPATH, INSERT_CELL_BELOW_ELEMENT).click()
        sleep(sleep_time)

    def execute_all(self, sleep_time: float = 0.5):
        for num, cell in enumerate(self.cells):
            error, output = self.execute_cell(cell)
            sleep(sleep_time)

            if error:
                print(f"[ERROR] Cell with num {num} caused an error")
                return False, num
        return True, None

    def change_cell(self, cell_num, new_cell_content: str):
        cell = self.cells[cell_num]
        edit_area = cell.find_element(By.XPATH, CELL_EDIT_AREA)
        actions = ActionChains(self.driver)

        actions.move_to_element(edit_area).click(edit_area)

        actions.key_down(Keys.COMMAND).send_keys("a").key_up(Keys.COMMAND).send_keys(
            Keys.BACKSPACE
        )

        actions.send_keys(new_cell_content)

        actions.perform()
        sleep(1)

    def __getitem__(self, cell_num: int):
        if cell_num >= len(self.cells):
            raise IndexError(
                f"Unexpected index number in list with size {len(self.cells)}"
            )

        return self.cells[cell_num]

    def restart_kernel(self):
        ZERO_KEY: str = "0"
        actions = (
            ActionChains(self.driver)
            .send_keys(Keys.ESCAPE)
            .send_keys(ZERO_KEY)
            .send_keys(ZERO_KEY)
            .send_keys(Keys.RETURN)
        )
        actions.perform()

    @staticmethod
    def get_cell_source(cell: WebElement) -> str:
        code_mirror_area = cell.find_element(By.XPATH, CELL_EDIT_AREA)
        return code_mirror_area.text

    def __str__(self):
        return self.sep.join([f"{self.get_cell_source(cell)}" for cell in self.cells])


if __name__ == "__main__":
    with SeleniumNotebook(
        notebook_path=Path(""),
        driver_path=Path(""),
        server=Path("http://localhost:8888/"),
    ) as ntb:
        error, num = ntb.execute_all()
        print(error)
        if num is not None:
            print(ntb.get_cell_output(ntb.cells[num]))

        # cell = ntb.cells[-1]
        # ntb.add_cell(cell)
        # ntb.change_cell(-1, "print('hello')")
        # ntb.execute_cell(ntb[-1])
        print(ntb)
