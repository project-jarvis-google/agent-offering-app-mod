"""Main Agent for the sub agent static_code_analysis_agent"""

from google.adk.agents import LlmAgent

from .config import MODEL
from .prompt import STATIC_CODE_ANALYSIS_PROMPT
from .static_code_analysis_tools import perform_static_code_analysis

static_code_analysis_agent = LlmAgent(
    name="static_code_analysis_agent",
    model=MODEL,
    description="Performs static code analysis and generates static code changes brief",
    instruction=STATIC_CODE_ANALYSIS_PROMPT,
    tools=[perform_static_code_analysis],
    disallow_transfer_to_parent=True,
)
