from google.adk.agents import LlmAgent

from .prompt import GCS_CODEBASE_STAGING_PROMPT
from .gcs_staging_tools import fetch_source_code_from_gcs_folder
from .config import MODEL

gcs_codebase_staging_agent = LlmAgent(
    name="gcs_codebase_staging_agent",
    model=MODEL,
    description="Agent for downloading application code from a GCS bucket into temporary storage.",
    instruction=GCS_CODEBASE_STAGING_PROMPT,
    tools=[fetch_source_code_from_gcs_folder],
)
