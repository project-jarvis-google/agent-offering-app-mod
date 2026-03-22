"""Main Agent for the sub agent context_analyzer_agent"""

from google.adk.agents import LlmAgent

from .config import MODEL
from .prompt import CONTEXT_ANALYZER_PROMPT
from .context_analyzer_tools import perform_context_analysis

context_analyzer_agent = LlmAgent(
    name="context_analyzer_agent",
    model=MODEL,
    description="Performs context analysis and generate context of the application",
    instruction=CONTEXT_ANALYZER_PROMPT,
    tools=[perform_context_analysis],
    disallow_transfer_to_parent=True,
)
