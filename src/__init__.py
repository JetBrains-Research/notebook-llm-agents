import logging
from pathlib import Path

ROOT_PATH: Path = Path(__file__).resolve().parent.parent


logging.basicConfig(
    filename=ROOT_PATH / "logs/actions.log",
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(message)s",
)

if __name__ == "__main__":
    print(ROOT_PATH)
