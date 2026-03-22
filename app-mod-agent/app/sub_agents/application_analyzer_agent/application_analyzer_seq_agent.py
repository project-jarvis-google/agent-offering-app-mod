from google.adk.agents import SequentialAgent

from .gcs_codebase_staging_agent.agent import gcs_codebase_staging_agent
from .parallel_application_analyzer_agent.agent import parallel_application_analyzer_agent
from .cloud_strategy_roadmap_agent.agent import cloud_strategy_roadmap_agent
from .report_generator_agent.agent import report_generator_agent

application_analyzer_seq_agent = SequentialAgent(
    name="application_analyzer_seq_agent",
    description="Executes a sequence of codebase fetching, parallel codebase analysis, and report generation.",
    sub_agents=[
        gcs_codebase_staging_agent,
        parallel_application_analyzer_agent,
        cloud_strategy_roadmap_agent,
        report_generator_agent,
    ],
)
