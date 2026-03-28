from google.adk.agents import LlmAgent

from ..config import MODEL
from .prompt import REPORT_GENERATOR_PROMPT

report_generator_agent = LlmAgent(
    name="report_generator_agent",
    model=MODEL,
    description="Agent for synthesizing the final technical analysis report",
    instruction=REPORT_GENERATOR_PROMPT,
)
