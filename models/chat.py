from typing import Literal, TypedDict


class Conversations(TypedDict):
    id: int
    title: str
    updated_at: str


class ChatMessage(TypedDict):
    role: Literal["user", "model"]
    timestamp: str
    content: str
