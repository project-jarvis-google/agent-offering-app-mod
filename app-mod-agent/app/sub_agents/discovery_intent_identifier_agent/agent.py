"""Main Agent for the sub agent discovery_intent_identifier_agent"""

from google.adk.agents import LlmAgent

from .config import MODEL
from .prompt import DISCOVERY_INTENT_PROMPT

from ..discovery_root_agent.discovery_tools import save_user_intent

discovery_intent_identifier_agent = LlmAgent(
    name="discovery_intent_identifier_agent",
    model=MODEL,
    description="Gathers user's migration intent, goals, and constraints.",
    instruction=DISCOVERY_INTENT_PROMPT,
    tools=[save_user_intent],
)
