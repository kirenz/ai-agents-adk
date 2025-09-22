"""Web-enabled agent example for the Google Agent Development Kit (ADK).

The agent wraps a LangChain Tavily search tool so the Gemini model can answer
questions by pulling in live web results. All code paths are annotated to highlight
what each call contributes to the final agent behaviour.

We lean on ``asyncio`` so the sample can await ADK's streaming events without
blocking. That keeps the agent responsive while tools run in the background and
mirrors how production web or CLI apps typically integrate ADK runners.
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

# These IDs keep the sample self-contained; production code would pass real values.
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
# `my_agent` exposes Gemini plus the Tavily tool so the model can decide when to search.
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
    """Spin up the short-lived session and runner that isolate each agent invocation.

    ADK treats sessions as the state container for a conversation. Keeping this helper
    separate makes it clear that every call gets a fresh context, so tests or demos do
    not bleed state into one another.
    """
    # The in-memory service is enough for demos; persistent apps would swap this out.
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )
    # Runner handles orchestrating the agent's tool invocations and streaming outputs.
    runner = Runner(agent=my_agent, app_name=APP_NAME, session_service=session_service)
    return session, runner


async def call_agent_async(query: str) -> None:
    """Convenience entry point that delivers a user query and prints the agent reply.

    This wrapper is what other scripts or notebooks import. It hides the Boilerplate
    around session setup and streaming so callers can simply await a response.
    """
    # ADK expects user input as `Content` objects; we wrap the raw string accordingly.
    content = types.Content(role="user", parts=[types.Part(text=query)])
    # Create fresh session context and an execution runner for this invocation.
    session, runner = await setup_session_and_runner()
    # `run_async` yields streaming events, including intermediate tool calls and the final answer.
    events = runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    async for event in events:
        if event.is_final_response():
            # The final event bundles the agent's concluding message; echo it to stdout.
            final_response = event.content.parts[0].text
            print("Agent Response:", final_response)
