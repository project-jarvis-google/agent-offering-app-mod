"""Main Agent for the sub agent google_search_dummy"""

from google.adk.agents import Agent
from google.adk.tools import google_search

from .config import MODEL
from .prompt import GOOGLE_SEARCH_PROMPT

google_search_dummy_agent = Agent(
    name="google_search_dummy_agent",
    model=MODEL,
    description="Agent to answer questions using Google Search.",
    instruction=GOOGLE_SEARCH_PROMPT,
    # google_search is a pre-built tool which allows the agent to perform Google searches.
    tools=[google_search],
)
