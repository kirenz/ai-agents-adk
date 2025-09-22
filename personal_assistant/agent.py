"""Simple personal assistant example using the Google Agent Development Kit (ADK).

The ADK expects each app to expose a `root_agent` instance. In this minimal demo we
configure a single large language model (LLM) agent that answers user questions.
"""

from google.adk.agents.llm_agent import Agent

# Instantiate the only agent we need. ADK launchers look for this name.
root_agent = Agent(
    model="gemini-2.5-flash",
    name="root_agent",
    description="A helpful assistant for user questions.",
    # System instruction that sets the assistant's tone; change it to tweak behaviour.
    instruction="Sei sarkastisch und unfreundlich.",
)
