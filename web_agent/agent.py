"""Web-enabled agent example for the Google Agent Development Kit (ADK).

The agent wraps a LangChain Tavily search tool so the Gemini model can answer
questions by pulling in live web results. All code paths are annotated to highlight
what each call contributes to the final agent behaviour.
"""

import asyncio
import os

from google.adk import Agent, Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.langchain_tool import LangchainTool
from google.genai import types
from langchain_community.tools import TavilySearchResults

# Fail fast if the Tavily API key is missing so beginners know why the tool fails.
if not os.getenv("TAVILY_API_KEY"):
    print("Warning: TAVILY_API_KEY environment variable not set. Web search will fail.")

APP_NAME = "news_app"
USER_ID = "1234"
SESSION_ID = "session1234"

# --- Tool setup --------------------------------------------------------------
# Configure the LangChain Tavily tool that performs the actual web search.
tavily_search = TavilySearchResults(
    max_results=5,
    search_depth="advanced",
    include_answer=True,
    include_raw_content=True,
    include_images=True,
)

# Wrap the LangChain tool so ADK can call it seamlessly.
adk_tavily_tool = LangchainTool(tool=tavily_search)

# --- Agent definition --------------------------------------------------------
# This agent can now invoke the Tavily search tool whenever Gemini decides it helps.
my_agent = Agent(
    name="langchain_tool_agent",
    model="gemini-2.0-flash",
    description="Agent to answer questions using TavilySearch.",
    instruction="I can answer your questions by searching the internet. Just ask me anything!",
    tools=[adk_tavily_tool],
)

# ADK launchers look for a variable named `root_agent` as the entry point.
root_agent = my_agent


async def setup_session_and_runner():
    """Create a temporary in-memory session plus the runner that executes the agent."""
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )
    runner = Runner(agent=my_agent, app_name=APP_NAME, session_service=session_service)
    return session, runner


async def call_agent_async(query: str) -> None:
    """Send a user query to the agent and stream the final response to stdout."""
    content = types.Content(role="user", parts=[types.Part(text=query)])
    session, runner = await setup_session_and_runner()
    events = runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    async for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text
            print("Agent Response:", final_response)


if __name__ == "__main__":
    # Allow `python web_agent/agent.py` to execute an empty query for quick smoke tests.
    asyncio.run(call_agent_async(""))
