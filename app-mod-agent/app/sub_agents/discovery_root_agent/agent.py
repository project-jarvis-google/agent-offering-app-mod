"""Main Agent for the sub agent discovery_root_agent"""

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

from .config import MODEL
from .prompt import DISCOVERY_ROOT_PROMPT
from .discovery_tools import save_user_intent

from ..discovery_intent_identifier_agent import discovery_intent_identifier_agent
from ..application_analyzer_agent.agent import application_analyzer_agent

discovery_root_agent = LlmAgent(
    name="discovery_root_agent",
    model=MODEL,
    description="Coordinates the discovery phase, gathering intent and triggering analysis.",
    instruction=DISCOVERY_ROOT_PROMPT,
    sub_agents=[
        discovery_intent_identifier_agent,
        application_analyzer_agent,
    ],
    tools=[
        save_user_intent,
    ]
)
