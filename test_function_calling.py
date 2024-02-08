import json
import os
from pathlib import Path

from dotenv import load_dotenv
from grazie.api.client.chat.prompt import ChatPrompt
from grazie.api.client.endpoints import GrazieApiGatewayUrls
from grazie.api.client.gateway import GrazieApiGatewayClient, AuthType, GrazieAgent
from grazie.api.client.llm_functions import FunctionDefinition
from grazie.api.client.llm_parameters import LLMParameters
from grazie.api.client.parameters import Parameters
from grazie.api.client.profiles import Profile
from omegaconf import OmegaConf

from src import ROOT_PATH
from src.preprocessing.process_notebook import notebook_to_string

env = load_dotenv()

error = """---------------------------------------------------------------------------
TypeError                                 Traceback (most recent call last)
Cell In[4], line 1
----> 1 print(2 + 'a')

TypeError: unsupported operand type(s) for +: 'int' and 'str'"""


if __name__ == "__main__":
    client = GrazieApiGatewayClient(
        grazie_agent=GrazieAgent(
            name="grazie-api-gateway-client-readme", version="dev"
        ),
        url=GrazieApiGatewayUrls.STAGING,
        auth_type=AuthType.USER,
        grazie_jwt_token=os.environ["GRAZIE_TOKEN"],
    )

    prompt_config = OmegaConf.load("prompts/fix_error_prompt_datalore.yaml")

    ntb_path = Path(ROOT_PATH / "data/test_notebooks/test_notebook.ipynb")
    ntb = notebook_to_string(ntb_path)
    response = client.chat(
        chat=ChatPrompt()
        .add_system("YOU MUST WRITE ONLY FUNCTION PARAMETERS")
        .add_user(
            prompt_config.user_prompt.format(notebook_source=ntb, error_trace=error)
        ),
        profile=Profile.OPENAI_GPT_4,
        parameters={
            LLMParameters.Functions: Parameters.JsonValue.from_functions(
                FunctionDefinition(
                    name="change_cell",
                    description="Change source of the existing cell in the notebook and execute it",
                )
                .add_argument(
                    name="cell_num",
                    description="Number of the cell in the notebook (starting from 0).",
                    _type=FunctionDefinition.FunctionParameterTypes.INTEGER,
                    required=True,
                )
                .add_argument(
                    name="cell_source",
                    description="New source of the cell which should be changed",
                    _type=FunctionDefinition.FunctionParameterTypes.STRING,
                    required=True,
                )
            ),
        },
    )
    print(response.function_call)
    print("=" * 10)
    out = json.loads(response.content)
    print(out)
