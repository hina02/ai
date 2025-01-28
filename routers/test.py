from dataclasses import dataclass, field

from fastapi import APIRouter, Depends
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter

from managers.chat import get_conversation, upsert_conversation
from managers.supabase import SupabaseManager
from routers.supabase import get_supabase_dev


@dataclass
class Deps:
    supabase: SupabaseManager
    title: str = ""
    conversation_id: int | None = None
    message_history: list[ModelMessage] = field(default_factory=list)


deps = Deps(supabase=SupabaseManager())

agent = Agent("gemini-1.5-pro", deps_type=Deps)
test_router = APIRouter()


@test_router.get("/test/chat/{conversation_id}")
async def chat(
    text: str, conversation_id: int, supabase: SupabaseManager = Depends(get_supabase_dev)
):
    message_history = get_conversation(supabase, conversation_id) if conversation_id else []

    # user_id, session_id for authorization
    user_id = supabase.get_user_id()

    agent = Agent("gemini-2.0-flash-exp")

    result = await agent.run(text, message_history=message_history)
    message_history = result.all_messages()
    message_history_json = ModelMessagesTypeAdapter.dump_json(message_history)
    upsert_conversation(supabase, user_id, "Chat", message_history_json, conversation_id)
    return result.data
