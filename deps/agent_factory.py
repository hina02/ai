from typing import Optional

from pydantic import BaseModel, Field
from pydantic_ai import Agent


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
