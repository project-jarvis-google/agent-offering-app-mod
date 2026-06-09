from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CreateWorkspaceRequest(BaseModel):
    name: str
    customer_name: str | None = None
    engagement_type: str | None = None
    opportunity_link: str
    deal_value: str
    source_type: Literal["github"] = "github"
    codebase_name: str = Field(..., description="Name of the application/service")
    source_value: str = Field(
        ..., description="GitHub repository URL (e.g., https://github.com/owner/repo)"
    )
    # included_files: list[str] = None  # Optional list of file names/paths to ingest
    token: str | None = Field(None, description="Optional GitHub Private Access Token")


# Pydantic model for API responses
class WorkspaceSchema(BaseModel):
    id: str
    name: str
    user_id: str
    created_at: datetime
    base_path: str
    customer_name: str | None = None
    engagement_type: str | None = None
    opportunity_link: str | None = None
    deal_value: str | None = None

    class Config:
        from_attributes = True


class IngestRequest(BaseModel):
    workspace_id: str = Field(
        ..., description="The ID of the user triggering ingestion"
    )
    source_type: Literal["github", "gitlab", "bitbucket"] = Field(
        "github", description="Type of the source data to be ingested"
    )
    source_value: str = Field(
        ..., description="GitHub, GitLab, or Bitbucket repository URL"
    )
    token: str | None = Field(None, description="Optional Private Access Token")
    source_label: str | None = Field(
        None, description="Label for the application/service"
    )
    model_config = ConfigDict(extra="ignore")


class IngestResponse(BaseModel):
    ws_id: str = Field(
        ..., description="The Workspace ID of triggering ingestion request"
    )
    status: str = Field(..., description="The current status of code ingestion")
    message: str = Field(
        ..., description="Message indicating the status of code ingestion"
    )


class SourceResponse(BaseModel):
    id: str
    workspace_id: str
    codebase_name: str | None = None
    repo_url: str
    gcs_destination_url: str
    status: str
    size: int | None = 0
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VerifyRepoRequest(BaseModel):
    source_type: Literal["github", "gitlab", "bitbucket"] = Field(
        "github", description="Type of the source data to be ingested"
    )
    source_value: str = Field(..., description="GitHub, GitLab, or Bitbucket repository URL")
    token: str | None = Field(None, description="Optional Private Access Token")


class VerifyRepoResponse(BaseModel):
    message: str = Field(..., description="Verification message")
    error_details: str | None = Field(None, description="Specific error details if any")
