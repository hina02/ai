from fastapi import APIRouter, Depends
from pydantic_ai.messages import ModelMessagesTypeAdapter

from managers.char_chat import Deps, char_chat
from managers.chat import get_conversation, upsert_conversation
from managers.supabase import SupabaseManager
from routers.supabase import get_supabase_dev

char_router = APIRouter()


@char_router.get("/char/chat/{conversation_id}")
async def chat(
    text: str,
    conversation_id: int,
    supabase: SupabaseManager = Depends(get_supabase_dev),
    ai_name: str = "",
    user_name: str = "",
):
    message_history = get_conversation(supabase, conversation_id) if conversation_id else []

    # user_id, session_id for authorization
    user_id = supabase.get_user_id()
    deps = Deps(supabase, ai_name=ai_name, user_name=user_name, conversation_id=conversation_id)
    result = await char_chat(text, message_history, deps)
    message_history = result.all_messages()
    message_history_json = ModelMessagesTypeAdapter.dump_json(message_history)
    upsert_conversation(supabase, user_id, "Chat", message_history_json, conversation_id)
    return result.data
