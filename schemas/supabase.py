from datetime import datetime

from pydantic import BaseModel, field_serializer
from pydantic_ai.messages import ModelMessage


class ConversationScehma(BaseModel):
    """all_messages() を保存する"""

    id: int | None = None
    title: str
    user_id: str
    messages: str
    updated_at: str
