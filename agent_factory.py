from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import logfire
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext, Tool

logfire.configure()


class AgentFactory(BaseModel):
    agents: dict = Field(default_factory=dict)

    def get_agent_names(self) -> list[str]:
        return list(self.agents.keys())

    async def run_agent(self, name: str, instruction: str) -> str:
        agent: Optional[Agent] = self.agents.get(name)
        if agent:
            assert isinstance(agent, Agent)
            response = await agent.run(instruction)
            return response.data
        return "Agent not found"

    async def create_agent(self, name: str, system_prompt: str) -> Agent:
        agent = Agent("gemini-1.5-pro", name=name, system_prompt=system_prompt)
        self.agents[name] = agent
        return "Success"

    async def save_agent(self):
        """Save created agent(system_prompt) to database."""
        pass


@dataclass
class FactoryDeps:
    factory: AgentFactory = field(default_factory=AgentFactory)


orchestrator = Agent(
    "openai:gpt-4o",
    deps_type=FactoryDeps,
    name="orchestrator",
    system_prompt="""You are the multiple agent orchestrator.
    You should assign any task to the agents to execute instruction.
    If you want to know available agents, you can get the agent names.
    If you want to run the agent, you can run the agent with the agent name and the instruction.

    You can also create the new instant agent.
    If you want to create the agent, you can create the agent with the agent name, system prompt and available tools by tool_names.
    If you want to know available tools, you can get the tool names.
    """,
)


@orchestrator.tool
def get_agent_names(ctx: RunContext[FactoryDeps]) -> RunContext[FactoryDeps]:
    return ctx.deps.factory.get_agent_names()


@orchestrator.tool
async def run_agent(ctx: RunContext[FactoryDeps], agent_name: str, instruction: str) -> str:
    return await ctx.deps.factory.run_agent(agent_name, instruction)


@orchestrator.tool
async def create_agent(ctx: RunContext[FactoryDeps], agent_name: str, system_prompt: str) -> Agent:
    return await ctx.deps.factory.create_agent(agent_name, system_prompt)


# sample usage
def get_today(_: RunContext):
    today = datetime.today()
    return today.strftime("%Y-%m-%d")


def get_weather(_: RunContext):
    return "It's sunny today."


def run_orchestrator_sample():
    default_agents = {
        "get_today": Agent("openai:gpt-4o-mini", tools=[Tool(get_today)]),
        "get_weather": Agent("openai:gpt-4o-mini", tools=[Tool(get_weather)]),
    }
    deps = FactoryDeps(tools=[], factory=AgentFactory(agents=default_agents))
    return orchestrator.run_sync(
        "Respond today's date and weather.",
        deps=deps,
    )
