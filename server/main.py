import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

from src.agents.proxy_agent import ProxyAgent
from src.manager.conversation_manager import ConversationManager


class ApiContent(BaseModel):
    agent_id: str
    message: str


class Item(BaseModel):
    session_uuid: str
    api_content: ApiContent


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

env = load_dotenv()
agent = ProxyAgent(token=os.environ["GRAZIE_TOKEN"])
manager = ConversationManager(agent=agent)


@app.post("/request/")
async def request_tool(req: Item):
    session_uuid = req.session_uuid
    message_raw = req.api_content.message

    message = manager.parse_environment_response(message_raw)
    instruction = manager.create_instruction(message)

    agent_response = manager.interact(prompt=instruction, session_uuid=session_uuid)
    print(agent_response)
    return agent_response


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
