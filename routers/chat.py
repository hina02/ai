import json
import uuid
from dataclasses import dataclass, field

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter

from managers.chat import (
    get_conversation,
    get_conversations,
    to_chat_message,
    upsert_conversation,
)
from managers.supabase import SupabaseManager
from models.chat import ChatMessage, Conversations
from routers.supabase import get_supabase, get_supabase_wb


@dataclass
class Deps:
    supabase: SupabaseManager
    title: str = ""
    conversation_id: int | None = None
    message_history: list[ModelMessage] = field(default_factory=list)


deps = Deps(supabase=SupabaseManager())

agent = Agent("gemini-1.5-pro", deps_type=Deps)
chat_router = APIRouter()


@chat_router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # get authenticated supabase instance with access token for message_history
    try:
        supabase: SupabaseManager = get_supabase_wb(
            access_token=websocket.headers.get("Authorization")
        )
        conversation_id = websocket.headers.get("conversation_id")
        message_history = get_conversation(supabase, conversation_id) if conversation_id else []
    except Exception as e:
        await websocket.send_json({"error": str(e)})
        await websocket.close()
        return

    # user_id, session_id for authorization
    user_id = supabase.get_user_id()
    session_id = str(uuid.uuid4())
    await websocket.send_json({"user_id": user_id, "session_id": session_id})

    agent = Agent("gemini-1.5-flash")

    # conversation loop
    try:
        while True:
            data = await websocket.receive_text()
            request: dict = json.loads(data)
            client_user_id = request.get("user_id", "")
            client_session_id = request.get("session_id", "")
            message = request.get("message", "")

            if client_user_id != user_id or client_session_id != session_id:
                await websocket.send_json({"error": "Unauthorized"})
                continue
            if not message:
                continue

            result = await agent.run(message, message_history=message_history)
            message_history = result.all_messages()
            await websocket.send_text(result.data)
    except WebSocketDisconnect:
        print("Client disconnected")

    # save conversation
    finally:
        if message_history:
            message_history_json = ModelMessagesTypeAdapter.dump_json(message_history)
            upsert_conversation(supabase, user_id, "Chat", message_history_json, conversation_id)


@chat_router.get("/chat/conversations")
def get_conversations_api(manager: SupabaseManager = Depends(get_supabase)) -> list[Conversations]:
    try:
        return get_conversations(manager)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversations: {str(e)}")


@chat_router.get("/chat/conversation/{conversation_id}")
def get_conversation_api(
    conversation_id: int, manager: SupabaseManager = Depends(get_supabase)
) -> list[ChatMessage]:
    try:
        conversation = get_conversation(manager, conversation_id)
        return [to_chat_message(m) for m in conversation]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversation: {str(e)}")
