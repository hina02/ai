from datetime import datetime

from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

from managers.supabase import SupabaseManager
from models.chat import ChatMessage, Conversations
from schemas.supabase import ConversationScehma


def get_conversations(manager: SupabaseManager) -> list[Conversations]:
    response = (
        manager.supabase.table("conversation")
        .select("id, title, updated_at")
        .order("updated_at", desc=True)
        .execute()
    )
    return [Conversations(**conversation) for conversation in response.data]


def get_conversation(manager: SupabaseManager, conversation_id: int) -> list[ModelMessage]:
    response = (
        manager.supabase.table("conversation")
        .select("messages")
        .eq("id", conversation_id)
        .execute()
    )
    if not response.data:
        return []
    conversation = response.data[0]["messages"]
    messages: list[ModelMessage] = []

    messages.extend(ModelMessagesTypeAdapter.validate_json(conversation))
    return messages


def upsert_conversation(
    manager: SupabaseManager,
    user_id: str,
    title: str,
    conversation_history: str,
    conversation_id: int | None = None,
) -> None:

    conversation = ConversationScehma(
        id=conversation_id,
        user_id=user_id,
        messages=conversation_history,
        updated_at=datetime.now().isoformat(),
        title=title,
    ).model_dump(exclude_none=True)
    manager.supabase.table("conversation").upsert(conversation).execute()


def to_chat_message(m: ModelMessage) -> ChatMessage:
    if isinstance(m, ModelRequest):
        first_part = m.parts[0]
        if isinstance(first_part, UserPromptPart):
            return ChatMessage(
                role="user", timestamp=first_part.timestamp.isoformat(), content=first_part.content
            )
    elif isinstance(m, ModelResponse):
        first_part = m.parts[0]
        if isinstance(first_part, TextPart):
            return ChatMessage(
                role="model", timestamp=m.timestamp.isoformat(), content=first_part.content
            )
    raise UnexpectedModelBehavior(f"Unexpected message type for chat app: {m}")
