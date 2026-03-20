from google.adk.agents import ParallelAgent

from ..context_analyzer_agent.agent import context_analyzer_agent
from ..dependency_analysis_agent.agent import dependency_analysis_agent
from ..static_code_analysis_agent.agent import static_code_analysis_agent

parallel_application_analyzer_agent = ParallelAgent(
    name="parallel_application_analyzer_agent",
    description="Runs parallel sub-agents to perform full application analysis",
    sub_agents=[
        context_analyzer_agent,
        dependency_analysis_agent,
        static_code_analysis_agent,
    ],
)
