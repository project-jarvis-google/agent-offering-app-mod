"""Main Agent for the sub agent dependency_analysis_agent"""

from google.adk.agents import LlmAgent

from .config import MODEL
from .prompt import DEPENDENCY_ANALYSIS_PROMPT
from .dependency_analysis_tools import perform_dependency_analysis

dependency_analysis_agent = LlmAgent(
    name="dependency_analysis_agent",
    model=MODEL,
    description="Performs dependency analysis and generate dependency maps",
    instruction=DEPENDENCY_ANALYSIS_PROMPT,
    tools=[perform_dependency_analysis],
    disallow_transfer_to_parent=True,
)
