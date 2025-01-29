import json
from dataclasses import dataclass, field

import logfire
from diskcache import Cache
from pydantic import BaseModel, Field, model_serializer
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelMessage
from pydantic_ai.result import RunResult

from managers.supabase import SupabaseManager


@dataclass
class Deps:
    supabase: SupabaseManager
    cache: Cache = Cache("/tmp/mycache")
    title: str = ""
    ai_name: str = ""
    user_name: str = ""
    conversation_id: int | None = None
    message_history: list[ModelMessage] = field(default_factory=list)


class Character(BaseModel):
    name: str
    profile: dict = Field(default_factory=dict)

    @model_serializer()
    def serialize_character(self):
        return f"{self.name}'s profile: {json.dumps(self.profile)}"


cache = Cache("/tmp/mycache")

agent = Agent(
    "openai:gpt-4o",
    deps_type=Deps,
    system_prompt="use save tool to save or memorize profile",
)


@agent.system_prompt
def get_ai_profile(ctx: RunContext[Deps]) -> str:
    char = ctx.deps.cache.get(ctx.deps.ai_name)
    if not char:
        char_data = ctx.deps.supabase.get_entity("character", ctx.deps.ai_name)
        char = Character(name=ctx.deps.user_name)
        char.profile = char_data["profile"] if char_data else {}
        ctx.deps.cache.set(char.name, char)
    return f"# Play a role as {char.name}. Your Personality: {char.model_dump_json()}"


@agent.system_prompt
def get_user_profile(ctx: RunContext[Deps]) -> str:
    char = ctx.deps.cache.get(ctx.deps.user_name)
    if not char:
        char_data = ctx.deps.supabase.get_entity("character", ctx.deps.user_name)
        logfire.info(f"char_data: {char_data}")
        char = Character(name=ctx.deps.user_name)
        char.profile = char_data["profile"] if char_data else {}
        ctx.deps.cache.set(ctx.deps.user_name, char)
    return f"Recognize User Personality: {char.model_dump_json()}"


@agent.tool
def get_character_profile(ctx: RunContext[Deps], character_name) -> str:
    char = ctx.deps.cache.get(character_name)
    if not char:
        char = ctx.deps.supabase.get_entity("character", character_name)
        char = Character(**char) if char else Character(name=character_name)
        ctx.deps.cache.set(char.name, char)
    return char.model_dump_json()


@agent.tool
async def udpate_character_profile(ctx: RunContext[Deps], name: str, profile: str):
    """profile: json string"""
    ctx.deps.supabase.save_entity("character", name, profile)
    char = Character(name=name, profile={"profile": profile})
    ctx.deps.cache.set(char.name, char)
    logfire.info(f"Character profile updated: {char}")
    return "Character profile updated"


async def char_chat(text: str, message_history: list[ModelMessage], deps: Deps) -> RunResult:
    return await agent.run(text, message_history=message_history, deps=deps)
