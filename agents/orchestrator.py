from dataclasses import dataclass, field
from datetime import datetime

from pydantic_ai import Agent, RunContext, Tool

from deps.agent_factory import AgentFactory


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


async def run_orchestrator_sample() -> str:
    default_agents = {
        "get_today": Agent("openai:gpt-4o-mini", tools=[Tool(get_today)]),
        "get_weather": Agent("openai:gpt-4o-mini", tools=[Tool(get_weather)]),
    }
    deps = FactoryDeps(factory=AgentFactory(agents=default_agents))
    return await orchestrator.run(
        "Respond today's date and weather.",
        deps=deps,
    )
