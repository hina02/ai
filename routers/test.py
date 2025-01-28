import base64
from dataclasses import dataclass, field

from fastapi import APIRouter, Depends, UploadFile
from openai.types.chat.chat_completion_content_part_image_param import ImageURL
from openai.types.chat.chat_completion_content_part_param import (
    ChatCompletionContentPartImageParam,
    ChatCompletionContentPartTextParam,
)
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


async def encode_image_to_base64(file: UploadFile):
    contents = await file.read()
    encoded_string = base64.b64encode(contents).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded_string}"


@test_router.post("/test/image_chat/{conversation_id}")
async def image_chat(text: str, files: list[UploadFile]):
    image_params = [
        ChatCompletionContentPartImageParam(
            type="image_url",
            image_url=ImageURL(url=await encode_image_to_base64(file), detail="low"),
        )
        for file in files
    ]
    agent = Agent("openai:gpt-4o-mini")
    result = await agent.run(
        [ChatCompletionContentPartTextParam(text=text, type="text"), *image_params]
    )
    return result.data
