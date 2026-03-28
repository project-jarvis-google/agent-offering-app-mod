"""Main Agent for the sub agent cloud_strategy_roadmap_agent"""

from google.adk.agents import LlmAgent
from google.adk.planners.plan_re_act_planner import PlanReActPlanner

from .config import MODEL
from .prompt import CLOUD_STRATEGY_ROADMAP_PROMPT
from .cloud_strategy_tools import perform_cloud_strategy_analysis

cloud_strategy_roadmap_agent = LlmAgent(
    name="cloud_strategy_roadmap_agent",
    model=MODEL,
    description="Performs cloud strategy analysis and generate roadmap",
    instruction=CLOUD_STRATEGY_ROADMAP_PROMPT,
    tools=[perform_cloud_strategy_analysis],
    planner=PlanReActPlanner(),
    disallow_transfer_to_parent=True,
)
