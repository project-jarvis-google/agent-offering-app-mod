import asyncio
import shutil
import tempfile
import uuid
import requests
from typing import List
from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends, Request
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sse_starlette.sse import EventSourceResponse

from app.core.workspace_manager import WorkspaceManager
from app.models.schemas import SourceResponse, IngestRequest, IngestResponse, CreateWorkspaceRequest, WorkspaceSchema
from app.models.domain import IngestionSource, WorkspaceModel, IngestionStatus
from app.core.database import get_db, AsyncSessionLocal
from app.utils.parsers import parse_github_url, parse_gcs_url
from app.services.github import download_github_repo
from app.services.gcs import upload_directory_to_gcs
from app.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/appmod", tags=["Workspaces"])

workspace_manager = WorkspaceManager()

async def background_ingestion_task(
    source_id: str,
    repo: str,
    owner: str,
    token: str | None,
    temp_dir: str,
    gcs_destination_path: str
):
    try:
        # Create a completely new session for the background task
        async with AsyncSessionLocal() as db:
            # Update to IN_PROGRESS
            result = await db.execute(select(IngestionSource).filter(IngestionSource.id == source_id))
            source = result.scalars().first()
            if source:
                source.status = IngestionStatus.PROCESSING
                await db.commit()            

            # Wrap synchronous network operations in threadpool so we don't block the event loop
            try:
                # 1. Download and extract from GitHub
                logger.info(f"[{source_id}] Downloading repository {owner}/{repo}...")
                extracted_dir = await run_in_threadpool(download_github_repo, owner, repo, temp_dir, token)
                
                # 2. Upload to GCS
                logger.info(f"[{source_id}] Uploading files to {gcs_destination_path}...")
                files_uploaded = await run_in_threadpool(upload_directory_to_gcs, extracted_dir, gcs_destination_path)
                
                logger.info(f"[{source_id}] Successfully ingested {owner}/{repo}. {files_uploaded} files uploaded.")
                
                source.status = IngestionStatus.COMPLETED
                await db.commit()

            except requests.exceptions.HTTPError as e:
                logger.error(f"[{source_id}] GitHub API Error: {e}")
                source.status = IngestionStatus.FAILED
                source.error_message = f"GitHub API Error: {e}"
                await db.commit()
            except Exception as e:
                logger.exception(f"[{source_id}] An unexpected error occurred: {e}")
                source.status = IngestionStatus.FAILED
                source.error_message = str(e)
                await db.commit()

    finally:
        logger.info(f"Cleaning up temporary directory: {temp_dir}")
        shutil.rmtree(temp_dir, ignore_errors=True)

@router.post("/ingest/sourcecode", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_repository(request: IngestRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """
    Ingests a GitHub repository asynchronously and uploads its contents to a GCS bucket.
    """
    try:
        logger.info(f"Received ingestion request for workspace id {request.ws_id} for repo name: {request.codebase_name} and repo url: {request.repo_url}")
        
        try:
            owner, repo = parse_github_url(request.repo_url)
        except ValueError as e:
            logger.error(f"Invalid GitHub URL: {e}")
            raise

        gcs_url = workspace_manager.get_workspace_path(request.ws_id)

        # Save initial state in DB
        new_codebase_source = IngestionSource(
            id=str(f"is-{uuid.uuid4().hex[:8]}"),
            workspace_id=request.ws_id,
            codebase_name=request.codebase_name,
            repo_url=request.repo_url,
            gcs_destination_url=gcs_url,
            status=IngestionStatus.PENDING,
            #TODO: Update size of repository
            size=0
        )
        db.add(new_codebase_source)
        await db.commit()
        await db.refresh(new_codebase_source)

        # Create a temporary directory
        temp_dir = tempfile.mkdtemp(prefix=f"ingest_{repo}_")
        
        # Enqueue background task
        background_tasks.add_task(
            background_ingestion_task,
            source_id=new_codebase_source.id,
            repo=repo,
            owner=owner,
            token=request.token,
            temp_dir=temp_dir,
            gcs_destination_path=gcs_url
        )

        return IngestResponse(
            ws_id=request.ws_id,
            status="QUEUED",
            message="Codebase ingestion queued successfully!"
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to create workspace: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspaces/{workspace_id}/source_files", response_model=List[SourceResponse])
async def get_sources(workspace_id: str, db: AsyncSession = Depends(get_db)):
    """Returns all ingestion sources for a given user"""
    # TODO: Implement security check to ensure user owns workspace
    # ws = workspace_manager.get_workspace(db, workspace_id, current_user.id)
    # if not ws:
    #     raise HTTPException(status_code=404, detail="Workspace not found")
    result = await db.execute(select(IngestionSource).filter(IngestionSource.workspace_id == workspace_id))
    return result.scalars().all()


#TODO: Implement source ingestion status streaming later 
# async def ingest_status_generator(request: Request, source_id: uuid.UUID):
#     while True:
#         if await request.is_disconnected():
#             break

#         # Need a fresh session instance to avoid caching stale data in long-running stream
#         async with AsyncSessionLocal() as db:
#             result = await db.execute(select(IngestionSource).filter(IngestionSource.id == source_id))
#             source = result.scalars().first()

#             if not source:
#                 yield {
#                     "event": "error",
#                     "data": f"Source {source_id} not found"
#                 }
#                 break

#             yield {
#                 "event": "message",
#                 "data": source.status
#             }

#             if source.status in ("SUCCESS", "FAILED"):
#                 break
        
#         await asyncio.sleep(2) # Poll every 2 seconds


# @router.get("/stream/{source_id}")
# async def stream_ingest_status(request: Request, source_id: uuid.UUID):
#     """Streams the real-time status of a job using Server-Sent Events"""
#     return EventSourceResponse(ingest_status_generator(request, source_id))


@router.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy"}
