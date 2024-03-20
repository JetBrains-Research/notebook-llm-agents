import json

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel


class ApiContent(BaseModel):
    agent_id: str
    message: str


class Item(BaseModel):
    api_content: ApiContent


app = FastAPI()


@app.post("/request/")
async def request_tool():
    response_content = input("Please enter response content: ")

    output = {
        "api_content": {
            "agent_id": "notebook",
        }
    }
    if response_content == "finish":
        tool = {
            "api_name": "finish",
            "args": {},
        }
    else:
        tool = {
            "api_name": "create_cell",
            "args": {"cell_source": f"# {response_content}"},
        }
    output["api_content"].update(tool)

    response = {"data": json.dumps(output)}
    return response


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
