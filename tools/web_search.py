from pydantic_ai import RunContext
from pydantic_ai.tools import ToolDefinition
from tavily import AsyncTavilyClient

from config import settings


async def tavily_websearch(ctx: RunContext, question) -> str:
    """Search the web for the answer to the question."""
    tavily_client = AsyncTavilyClient(settings.tavily_api_key)
    answer = await tavily_client.qna_search(query=question)
    return answer


# tool preparation (e.g., tools=[Tool(websearch_tool, prepare=check_tavily_api_key)])
async def check_tavily_api_key(_, tool_def: ToolDefinition) -> ToolDefinition | None:
    api_key = settings.tavily_api_key

    if api_key:
        return tool_def
