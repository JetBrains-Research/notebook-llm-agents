from grazie.api.client.llm_functions import FunctionDefinition
from grazie.api.client.llm_parameters import LLMParameters
from grazie.api.client.parameters import Parameters

notebook_tools_grazie = {
    LLMParameters.Functions: Parameters.JsonValue.from_functions(
        FunctionDefinition(
            name="change_cell",
            description="Change source of the existing cell in the notebook and execute it, "
            "returns the output of the cell",
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
        ),
        FunctionDefinition(
            name="execute_cell",
            description="Executing cell in the notebook without changing its code, returns the output of the cell ",
        ).add_argument(
            name="cell_num",
            description="Number of the cell in the notebook (starting from 0).",
            _type=FunctionDefinition.FunctionParameterTypes.INTEGER,
            required=True,
        ),
        FunctionDefinition(
            name="add_cell",
            description="Append new cell in the notebook and execute it, returns the output of the cell ",
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
        ),
        FunctionDefinition(
            name="finish",
            description="Indicates finishing solving the error and re-executed cell with the error to check it.",
        ),
    ),
}
