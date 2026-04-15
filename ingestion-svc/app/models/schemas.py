from typing import Literal
from pydantic import BaseModel, Field
from typing import Optional
import uuid
from datetime import datetime

class CreateWorkspaceRequest(BaseModel):
    name: str
    customer_name: str | None = None
    engagement_type: str | None = None
    opportunity_link: str
    deal_value: str
    source_type: Literal["github"] = "github"
    codebase_name: str = Field(..., description="Name of the application/service")
    source_value: str = Field(..., description="GitHub repository URL (e.g., https://github.com/owner/repo)")
    # included_files: list[str] = None  # Optional list of file names/paths to ingest
    token: Optional[str] = Field(None, description="Optional GitHub Private Access Token")

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
    ws_id: str = Field(..., description="The ID of the user triggering ingestion")
    repo_url: str = Field(..., description="GitHub repository URL (e.g., https://github.com/owner/repo)")
    token: Optional[str] = Field(None, description="Optional GitHub Private Access Token")
    codebase_name: str = Field(..., description="Name of the application/service")

class IngestResponse(BaseModel):
    ws_id: str = Field(..., description="The Workspace ID of triggering ingestion request")
    status: str = Field(..., description="The current status of code ingestion")
    message: str = Field(..., description="Message indicating the status of code ingestion")

class SourceResponse(BaseModel):
    id: str
    workspace_id: str
    codebase_name: str
    repo_url: str
    gcs_destination_url: str
    status: str
    size: Optional[int] = 0
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class VerifyRepoRequest(BaseModel):
    github_url: str = Field(..., description="GitHub repository URL")
    pat_token: Optional[str] = Field(None, description="Optional GitHub Private Access Token")

class VerifyRepoResponse(BaseModel):
    message: str = Field(..., description="Verification message")
    error_details: Optional[str] = Field(None, description="Specific error details if any")
