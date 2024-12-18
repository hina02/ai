from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from enum import Enum
import json
from dotenv import load_dotenv
from dataclasses import dataclass, field
from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.tools import ToolDefinition
from pydantic_ai.messages import ModelMessage
import logfire

load_dotenv()
logfire.configure()  
logfire.instrument_asyncpg()  

app = FastAPI()

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    message_history: list[ModelMessage] = []
    agent = Agent('gemini-1.5-flash')

    try:
        while True:
            data = await websocket.receive_text()
            request: dict = json.loads(data)

            message = request.get("message", "")
            result = await agent.run(message, message_history=message_history)
            message_history = result.all_messages()
            await websocket.send_text(result.data)
    except WebSocketDisconnect:
        print("Client disconnected")


@app.get("/")
def read_root():
    return {"Hello": "World"}
