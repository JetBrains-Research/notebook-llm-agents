from pathlib import Path

ROOT_PATH: Path = Path(__file__).resolve().parent.parent


if __name__ == '__main__':
    print(ROOT_PATH)