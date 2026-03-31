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
from app.models.schemas import SourceResponse, CreateWorkspaceRequest, WorkspaceSchema
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


# Add workspace endpoints
@router.post("/workspaces", response_model=WorkspaceSchema, status_code=status.HTTP_202_ACCEPTED)
async def create_workspace(
    req: CreateWorkspaceRequest,
    background_tasks: BackgroundTasks,
    #TODO: Implement firebase auth to fetch user id
    # current_user: auth.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    #TODO: Implement firebase auth to fetch user id
    # existing_ws = (
    #     db.query(WorkspaceModel)
    #     .filter(
    #         WorkspaceModel.user_id == current_user.id,
    #         func.lower(WorkspaceModel.name) == req.name.lower(),
    #     )
    #     .first()
    # )

    # if existing_ws:
    #     raise HTTPException(
    #         status_code=status.HTTP_409_CONFLICT,
    #         detail=f"A workspace with the name '{req.name}' already exists.",
    #     )

    """Creates a new workspace and triggers data ingestion."""
    try:
        ws = await workspace_manager.create_workspace(
            db,
            req.name,
            #TODO: Change temp user id to actual user id
            "temp-uuid",
            customer_name=req.customer_name,
            engagement_type=req.engagement_type,
            opportunity_link=req.opportunity_link,
            deal_value=req.deal_value,
        )

        #TODO: Implement something similar for repositories
        # if req.included_files:
        #     for fname in req.included_files:
        #         fr = FileRecordModel(
        #             id=f"fr-{uuid.uuid4().hex[:8]}",
        #             workspace_id=ws.id,
        #             file_name=fname,
        #             source_url=req.source_value,
        #             status=FileStatus.PENDING,
        #         )
        #         db.add(fr)
        #     db.commit()

        # Trigger Ingestion in Background
        logger.info(f"Triggering background ingestion for workspace {ws.id}")

        # We must pass the DB Session logic carefully.
        # Passing 'db' directly to background task is risky as request session closes.
        # Ideally IngestionService should create its own session or we assume simpler logic.
        # But here IngestionService is synchronous logic.
        # We can't easily pass the 'db' session because it closes after request.
        # Hack: Pass a new session factory or handle session inside ingestion?
        # Better: IngestionService should create a new session.

        # Let's adjust IngestionService call signature in server.py to NOT take db,
        # and let IngestionService create it? Or pass a session factory?

        # For this step, I'll pass the session factory to the background task wrapper

        # def run_ingestion_background(
        #     workspace_base, s_type, s_value, w_id, inc_files, token
        # ):
        #         try:
        #         ingestion_service.ingest_data(
        #             workspace_base, s_type, s_value, w_id, inc_files, token=token
        #         )
        #         except Exception as e:
        #         logger.error(f"Background ingestion failed: {e}")

        # background_tasks.add_task(
        #     run_ingestion_background,
        #     ws.base_path,
        #     req.source_type,
        #     req.source_value,
        #     ws.id,
        #     req.included_files,
        #     req.token
        # )

        await ingest_repository(ws_id=ws.id, repo_url=req.source_value, token=req.token, codebase_name=req.codebase_name, gcs_url=f"{ws.base_path}/{req.codebase_name}", background_tasks=background_tasks, db=db)

        return ws

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to create workspace: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# @router.post("/ingest/sourcecode", response_model=SourceResponse, status_code=status.HTTP_202_ACCEPTED)
# async def ingest_repository(request: IngestRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
#     """
#     Ingests a GitHub repository asynchronously and uploads its contents to a GCS bucket.
#     """
async def ingest_repository(ws_id: str, repo_url: str, token: str, codebase_name: str, gcs_url: str,  background_tasks: BackgroundTasks, db: AsyncSession):
    logger.info(f"Received ingestion request for workspace id {ws_id} for repo: {repo_url} to GCS: {gcs_url}")
    
    try:
        owner, repo = parse_github_url(repo_url)
    except ValueError as e:
        logger.error(f"Invalid GitHub URL: {e}")
        raise

    try:
        bucket, prefix = parse_gcs_url(gcs_url)
    except ValueError as e:
        logger.error(f"Invalid GCS URL: {e}")
        raise

    # Save initial state in DB
    new_codebase_source = IngestionSource(
        id=str(f"is-{uuid.uuid4().hex[:8]}"),
        workspace_id=ws_id,
        codebase_name=codebase_name,
        repo_url=repo_url,
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
        token=token,
        temp_dir=temp_dir,
        gcs_destination_path=gcs_url
    )

    # return new_source


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
