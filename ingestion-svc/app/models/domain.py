import uuid
import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class WorkspaceModel(Base):
    """SQLAlchemy model for Workspaces."""
    __tablename__ = "workspaces"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    # user_id now stores the Firebase UID (string)
    user_id = Column(String, nullable=False, index=True)
    base_path = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc))
    
    # New Fields
    customer_name = Column(String, nullable=True)
    engagement_type = Column(String, nullable=True)
    opportunity_link = Column(String, nullable=True)
    deal_value = Column(String, nullable=True)

class IngestionStatus:
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class IngestionSource(Base):
    __tablename__ = "ingestion_sources"

    id = Column(String, primary_key=True)
    workspace_id = Column(String, index=True, nullable=False)
    codebase_name = Column(String, nullable=False)
    repo_url = Column(String, nullable=False)
    gcs_destination_url = Column(String, nullable=False)
    status = Column(String, nullable=False, default=IngestionStatus.PENDING)
    size = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc), onupdate=datetime.datetime.now(datetime.timezone.utc))
