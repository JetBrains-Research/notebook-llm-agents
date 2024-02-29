# Python Package: LLM Agents for Solving Errors in Notebooks

---

## Key Features

- Reads and processes Jupyter notebooks
- Identifies various forms of Python errors
- ...

---

## Installation

### Dependencies

To install the package using poetry clone it and install the necessary dependencies

```shell
poetry shell (optional)
poetry install
```

### Environmental Variables

Add needed environmental variables:

- `GRAZIE_TOKEN`: Grazie developer token to use LLMs
- `CHROMIUM_DRIVER_PATH`: Path to [chromium driver](https://chromedriver.chromium.org/downloads) executable. _Note, that
  additionally to the driver, Chrome or Chrome-based browser should be installed._

You can add environmental variables by just adding them into `.env` file in the root of the project.

To check that all environmental variables are added, execute the following command:

```shell
poetry run check-env 
```

### Docker

To interact with Jupyter notebook from Docker environment, the Docker should be installed. Also, all needed data and
requirements should be specified in [remote environment  folder.](remote_environment)

---

## How to Use

Build docker image

```shell
cd remote_environment
docker build -t agent-jupyter-interaction-docker-image .
cd .. 
```

To interact on single notebook:

```shell
poetry run python3 single_notebook_interaction.py
```

To run benchmark on set of notebooks:

```shell
poetry run python3 run_benchmark.py
```

---

## Support

If you have any questions or find a bug, please report them on our GitHub issue tracker.

## Contributing

We welcome contributions from the open-source community. From fixing typos, bugs to implementing new features, feel free
to fork this project and create a pull request.

*Disclaimer*

*This package is still under active development. We're actively adding new features and improving its functionality. Any
change to the package will be reflected in this README.*