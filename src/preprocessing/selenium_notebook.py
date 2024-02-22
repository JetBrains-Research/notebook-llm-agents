from pathlib import Path
from time import sleep

from src.preprocessing.notebook import NotebookBase
from typing import Optional

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains


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

    def __enter__(self):
        service = Service(executable_path=str(self.driver_path))
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("headless")
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.get(str(self.server / "notebooks/" / self.notebook_path))
        sleep(5)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()

    @property
    def cells(self):
        cell_xpath = "//div[contains(@class, 'lm-Widget') and contains(@class, 'jp-Cell') and contains(@class, 'jp-CodeCell') and contains(@class, 'jp-Notebook-cell')]"
        return self.driver.find_elements(By.XPATH, cell_xpath)

    @staticmethod
    def get_cell_output(cell: WebElement):
        output = ""
        try:
            output_location = ".//div[contains(@class, 'jp-OutputArea-output')]"
            cell_outputs = cell.find_elements(By.XPATH, output_location)
            output = "".join([output.text for output in cell_outputs])
        except Exception as e:
            print("Error while printing cell output:", str(e))
        finally:
            return output

    @staticmethod
    def _wait_for_execution(cell: WebElement):
        wait_time = 0
        delta = 0.1
        while True:
            try:
                cell.find_element(
                    By.XPATH,
                    ".//*[contains(text(), '[*]') or contains(text(), 'In [*]')]",
                )
                # print(f"Cell is still running. Waiting for {wait_time} seconds.")
                sleep(delta)
                wait_time += delta
            except NoSuchElementException:
                # print("Cell finished execution.")
                break

    def execute_cell(self, cell: WebElement):
        cell.click()
        action = (
            ActionChains(self.driver)
            # .send_keys(Keys.END)
            # .send_keys(Keys.ENTER)
            .key_down(Keys.COMMAND)
            .key_down(Keys.ENTER)
        )
        action.perform()
        self._wait_for_execution(cell)
        output = self.get_cell_output(cell)
        error = True if "Traceback (most recent call last)" in output else False
        return error, output

    def add_cell(self, current_cell: Optional[WebElement] = None):
        insert_cell_xpath: str = '//button[@data-command="notebook:insert-cell-below"]'
        cell = (
            current_cell
            if current_cell is not None
            else self.driver.find_element(
                By.XPATH, "//div[contains(@class, 'jp-Notebook-cell')][last()]"
            )
        )
        cell.click()
        self.driver.find_element(By.XPATH, insert_cell_xpath).click()
        sleep(1)

    def execute_all(self):
        for num, cell in enumerate(self.cells):
            error, output = self.execute_cell(cell)
            sleep(0.5)

            if error:
                print(f"[ERROR] Cell with num {num} caused an error")
                return False, num
        return True, None

    def change_cell(self, cell_num, new_cell_content: str):
        cell = self.cells[cell_num]
        edit_area = cell.find_element(By.XPATH, ".//div[@class='cm-content']")
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
        actions = (
            ActionChains(self.driver)
            .send_keys(Keys.ESCAPE)
            .send_keys("0")
            .send_keys("0")
            .send_keys(Keys.RETURN)
        )
        actions.perform()

    @staticmethod
    def get_cell_source(cell: WebElement) -> str:
        code_mirror_area = cell.find_element(By.XPATH, ".//div[@class='cm-content']")
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
