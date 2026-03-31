from sqlalchemy.ext.asyncio import AsyncSession
import logging
import os
import shutil
import uuid
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

from google.auth import credentials as google_auth_credentials
from google.cloud import storage
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.domain import WorkspaceModel
from app.models.schemas import WorkspaceSchema

load_dotenv()
logger = logging.getLogger(__name__)

class WorkspaceManager:
    def __init__(self, root_data_dir: str = None):
        # self.SessionLocal = db_session_factory  <-- Removed

        
        # Check if we are using GCS or Local
        self.bucket_name = os.getenv("INSIGHTWAVE_WORKSPACE_BUCKET")

        self.storage_client = storage.Client()
        self.use_gcs = True
        logger.info(f"WorkspaceManager initialized in GCS mode. Bucket: {self.bucket_name}")
        
        # Auto-detect Service Account Email if not explicitly set
        # sa_email = os.getenv("SIGNING_SA_EMAIL")
        # if not sa_email:
        #     try:
        #         # Try to get from storage client credentials
        #         if hasattr(self.storage_client._credentials, 'service_account_email'):
        #             sa_email = self.storage_client._credentials.service_account_email
                
        #         # Fallback for generic 'default' or missing email in credentials
        #         if not sa_email or sa_email == 'default':
        #             import google.auth
        #             creds, _ = google.auth.default()
        #             if hasattr(creds, 'service_account_email'):
        #                 sa_email = creds.service_account_email
        #     except Exception as e:
        #         logger.warning(f"Error checking GCS credentials for email: {e}")

    def _get_workspace_path(self, workspace_id: str) -> str:
        if self.use_gcs:
            return f"gs://{self.bucket_name}/workspaces/{workspace_id}"

    async def create_workspace(self, db: AsyncSession, name: str, user_id: str, 
                         customer_name: str = None, engagement_type: str = None,
                         opportunity_link: str = None, deal_value: str = None) -> WorkspaceSchema:
        """Creates a new workspace entry in DB."""
        workspace_id = f"ws-{uuid.uuid4().hex[:8]}"
        base_path = self._get_workspace_path(workspace_id)

        # In GCS, directories are virtual, so we don't need os.makedirs.
        # We just create the DB record. The IngestionService will create the blobs.
        if not self.use_gcs:
            for d in ["source_files", "raw", "artifacts", "debug"]:
                os.makedirs(os.path.join(base_path, d), exist_ok=True)

        db_workspace = WorkspaceModel(
            id=workspace_id,
            name=name,
            user_id=user_id,
            base_path=base_path,
            customer_name=customer_name,
            engagement_type=engagement_type,
            opportunity_link=opportunity_link,
            deal_value=deal_value
        )
        db.add(db_workspace)
        await db.commit()
        await db.refresh(db_workspace)

        logger.info(f"Created workspace {workspace_id} for user {user_id} at {base_path}")
        return WorkspaceSchema.model_validate(db_workspace)

    async def get_workspace(self, db: AsyncSession, workspace_id: str, user_id: str) -> WorkspaceSchema | None:
        """Retrieves workspace metadata if it belongs to the user."""
        result = await db.execute(select(WorkspaceModel).filter(
            WorkspaceModel.id == workspace_id,
            WorkspaceModel.user_id == user_id
        ))
        workspace = result.scalars().first()

        if workspace:
            return WorkspaceSchema.model_validate(workspace)
        return None

    async def list_workspaces(self, db: AsyncSession, user_id: str) -> list[WorkspaceSchema]:
        """Lists all workspaces belonging to a specific user."""
        result = await db.execute(select(WorkspaceModel).filter(
            WorkspaceModel.user_id == user_id
        ).order_by(WorkspaceModel.created_at.desc()))
        workspaces = result.scalars().all()

        return [WorkspaceSchema.model_validate(ws) for ws in workspaces]

    async def list_artifacts(self, db: AsyncSession, workspace_id: str, user_id: str) -> list[dict]:
        """Lists files in the artifacts directory of a workspace with metadata."""
        workspace = await self.get_workspace(db, workspace_id, user_id)
        if not workspace:
            return []
        
        files = []
        if self.use_gcs:
            # Parse gs://bucket/path
            prefix = workspace.base_path.replace(f"gs://{self.bucket_name}/", "") + "/artifacts/"
            blobs = self.storage_client.list_blobs(self.bucket_name, prefix=prefix)
            
            for b in blobs:
                if b.name.endswith('/'): continue
                files.append({
                    "name": b.name.split('/')[-1],
                    "size": b.size,
                    "type": "file" # Extension logic can be handled in frontend or here
                })
        else:
            artifacts_dir = os.path.join(workspace.base_path, "artifacts")
            if os.path.exists(artifacts_dir):
                for root, _, filenames in os.walk(artifacts_dir):
                    for f in filenames:
                        if f.startswith('.'): continue
                        f_path = os.path.join(root, f)
                        # Create relative path for display if needed, or just use filename
                        # Currently frontend seems to expect just name, but let's see. 
                        # If we return "Folder/File.ext", frontend needs to handle it.
                        rel_path = os.path.relpath(f_path, artifacts_dir)
                        files.append({
                            "name": rel_path,
                            "size": os.path.getsize(f_path),
                            "type": "file"
                        })
        return files

    async def list_raw_files(self, db: AsyncSession, workspace_id: str, user_id: str) -> list[dict]:
        """Lists files in the raw directory with metadata."""
        workspace = await self.get_workspace(db, workspace_id, user_id)
        if not workspace:
            return []
        
        files = []
        if self.use_gcs:
            prefix = workspace.base_path.replace(f"gs://{self.bucket_name}/", "") + "/source_files/"
            blobs = self.storage_client.list_blobs(self.bucket_name, prefix=prefix)
            for b in blobs:
                if b.name.endswith('/'): continue
                files.append({
                    "name": b.name.split('/')[-1],
                    "size": b.size,
                    "type": "file"
                })
        else:
            source_files_dir = os.path.join(workspace.base_path, "source_files")
            if os.path.exists(source_files_dir):
                for root, _, filenames in os.walk(source_files_dir):
                    for f in filenames:
                        if f.startswith('.'): continue
                        f_path = os.path.join(root, f)
                        rel_path = os.path.relpath(f_path, source_files_dir)
                        files.append({
                            "name": rel_path,
                            "size": os.path.getsize(f_path),
                            "type": "file"
                        })
        return files


    # def get_file_url(self, db: Session, workspace_id: str, user_id: str, filename: str) -> str | None:
    #     """
    #     Retrieves a download URL (GCS signed URL) or local path for a file.
    #     Searches 'artifacts' first, then 'raw'.
    #     """
    #     workspace = self.get_workspace(db, workspace_id, user_id)
    #     logger.info(f"Workspace: {workspace}")
    #     if not workspace:
    #         return None

    #     # Priority: source_files -> artifacts -> raw
    #     for sub_dir in ["source_files", "artifacts", "raw"]:
    #         if self.use_gcs:
    #             blob_name = workspace.base_path.replace(f"gs://{self.bucket_name}/", "") + f"/{sub_dir}/{filename}"
    #             print(f"File name: {filename}")
    #             bucket = self.storage_client.bucket(self.bucket_name)
    #             blob = bucket.blob(blob_name)
                
    #             if blob.exists():
    #                 logger.info(f"Generating signed URL for {blob_name}")
    #                 # Generate a signed URL valid for 1 hour
    #                 # If IAM signer is configured, use it. Otherwise use default creds.
    #                 creds = self.iam_signer if (self.iam_signer and self.iam_signer.service_account_email) else None
                    
    #                 return blob.generate_signed_url(
    #                     version="v4",
    #                     expiration=3600,  # 1 hour
    #                     method="GET",
    #                     credentials=creds
    #                 )
    #         else:
    #             file_path = os.path.join(workspace.base_path, sub_dir, filename)
    #             logger.info(f"File path: {file_path}")
    #             if os.path.exists(file_path):
    #                 return file_path

    #     return None

    async def delete_workspace(self, db: AsyncSession, workspace_id: str, user_id: str) -> bool:
        """Deletes a workspace from DB and disk if it belongs to the user."""
        # 1. Check ownership and existence
        result = await db.execute(select(WorkspaceModel).filter(
            WorkspaceModel.id == workspace_id,
            WorkspaceModel.user_id == user_id
        ))
        workspace = result.scalars().first()

        if not workspace:
            logger.warning(f"Delete failed: Workspace {workspace_id} not found or access denied for user {user_id}")
            return False

        # Delete from Storage
        if self.use_gcs:
            try:
                prefix = workspace.base_path.replace(f"gs://{self.bucket_name}/", "")
                blobs = list(self.storage_client.list_blobs(self.bucket_name, prefix=prefix))
                if blobs:
                    bucket = self.storage_client.bucket(self.bucket_name)
                    bucket.delete_blobs(blobs)
                    logger.info(f"Deleted {len(blobs)} blobs from GCS for workspace {workspace_id}")
            except Exception as e:
                logger.error(f"Failed to delete GCS blobs: {e}")
        else:
            import shutil
            if os.path.exists(workspace.base_path):
                try:
                    shutil.rmtree(workspace.base_path)
                except Exception as e:
                    logger.error(f"Failed to delete directory: {e}")

        # Delete from DB
        await db.delete(workspace)
        await db.commit()
        logger.info(f"Deleted workspace {workspace_id}")
        return True
