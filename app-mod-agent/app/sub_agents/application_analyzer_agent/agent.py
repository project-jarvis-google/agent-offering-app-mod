"""Main Agent for the sub agent application_analyzer_agent"""

from google.adk.agents import LlmAgent

from .config import MODEL
from .prompt import APPLICATION_ANALYZER_PROMPT

from .application_analyzer_seq_agent import application_analyzer_seq_agent

application_analyzer_agent = LlmAgent(
    name="application_analyzer_agent",
    model=MODEL,
    description="Performs high-level technical analysis of a codebase sourced from GCS.",
    instruction=APPLICATION_ANALYZER_PROMPT,
    sub_agents=[application_analyzer_seq_agent],
)
