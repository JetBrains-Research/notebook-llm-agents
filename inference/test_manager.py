import os
from pathlib import Path

from omegaconf import OmegaConf
from single_notebook_interaction import SafeDockerContainer

from src import ROOT_PATH
from src.agents.proxy_agent import ProxyAgent
from src.manager.conversation_manager import ConversationManager
from src.preprocessing.selenium_notebook import SeleniumNotebook

if __name__ == "__main__":
    experiment_config = OmegaConf.load(ROOT_PATH / "inference/single_notebook_interaction_config.yaml")
    docker_params = OmegaConf.to_container(experiment_config.docker_params)

    notebook_path = Path(experiment_config.notebook_params.notebook_path)
    notebook_server = Path(experiment_config.notebook_params.notebook_server)

    container = SafeDockerContainer(docker_params)
    with container:
        notebook = SeleniumNotebook(
            driver_path=Path(os.environ["CHROMIUM_DRIVER_PATH"]),
            notebook_path=notebook_path,
            server=notebook_server,
            headless=False,
        )

        with notebook as notebook:
            notebook.restart_kernel()
            success, error_cell_num = notebook.execute_all()
            if success:
                print("No error occured")
                exit()

            error_trace = notebook.get_cell_output(notebook.cells[error_cell_num])
            notebook_source = str(notebook)

            prompt_config = OmegaConf.load("prompts/fix_error_prompt_custom.yaml")
            message = prompt_config.get("user_prompt").format(
                notebook_source=notebook_source,
                error_trace=error_trace,
                cell_amount=len(notebook.cells),
                cell_num=error_cell_num,
            )

            agent = ProxyAgent(token=os.environ["GRAZIE_TOKEN"])
            manager, session_uuid = ConversationManager(agent=agent, environment=notebook), ""

            while not success:
                agent_response = manager.iterate(prompt=message, session_uuid=session_uuid)
                print(f"Agent response is {agent_response}")

                if agent_response is True:
                    print(f"finish session {session_uuid}")
                    success = True
                    break

                session_uuid = agent_response.get("session_uuid")

                error, env_response = manager.execute_tools(agent_response)
                env_response = manager.parse_environment_response(env_response)
                env_response = manager.create_instruction(env_response)

                print(f"Env response if {env_response}")

                message = env_response
