import shutil
import tempfile
import uuid

import requests
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import AsyncSessionLocal, get_db
from app.core.logger import get_logger
from app.core.workspace_manager import WorkspaceManager
from app.models.domain import IngestionSource, IngestionStatus
from app.models.schemas import (
    IngestRequest,
    IngestResponse,
    SourceResponse,
    VerifyRepoRequest,
    VerifyRepoResponse,
)
import urllib.parse
from app.services.gcs import upload_directory_to_gcs
from app.services.github import download_github_repo
from app.services.gitlab import download_gitlab_repo
from app.services.bitbucket import download_bitbucket_repo
from app.utils.parsers import parse_github_url, parse_gitlab_url, parse_bitbucket_url

logger = get_logger(__name__)

router = APIRouter(prefix="/app-mod", tags=["Workspaces"])

workspace_manager = WorkspaceManager()


async def background_ingestion_task(
    source_id: str,
    source_value: str,
    token: str | None,
    temp_dir: str,
    gcs_destination_path: str,
):
    try:
        # Create a completely new session for the background task
        async with AsyncSessionLocal() as db:
            # Update to IN_PROGRESS
            result = await db.execute(
                select(IngestionSource).filter(IngestionSource.id == source_id)
            )
            source = result.scalars().first()
            if source:
                source.status = IngestionStatus.PROCESSING
                await db.commit()

            # Wrap synchronous network operations in threadpool so we don't block the event loop
            try:
                # 1. Download and extract from the source platform
                if "github.com" in source_value:
                    owner, repo = parse_github_url(source_value)
                    logger.info(f"[{source_id}] Downloading GitHub repository {owner}/{repo}...")
                    extracted_dir = await run_in_threadpool(
                        download_github_repo, owner, repo, temp_dir, token
                    )
                elif "gitlab.com" in source_value:
                    full_path, repo = parse_gitlab_url(source_value)
                    logger.info(f"[{source_id}] Downloading GitLab repository {full_path}...")
                    extracted_dir = await run_in_threadpool(
                        download_gitlab_repo, full_path, repo, temp_dir, token
                    )
                elif "bitbucket.org" in source_value:
                    workspace, repo = parse_bitbucket_url(source_value)
                    logger.info(f"[{source_id}] Downloading Bitbucket repository {workspace}/{repo}...")
                    extracted_dir = await run_in_threadpool(
                        download_bitbucket_repo, workspace, repo, temp_dir, token
                    )
                else:
                    raise ValueError(f"Unsupported repository host in URL: {source_value}")

                # 2. Upload to GCS
                logger.info(
                    f"[{source_id}] Uploading files to {gcs_destination_path}..."
                )
                files_uploaded = await run_in_threadpool(
                    upload_directory_to_gcs, extracted_dir, gcs_destination_path
                )

                logger.info(
                    f"[{source_id}] Successfully ingested {source_value}. {files_uploaded} files uploaded."
                )

                source.status = IngestionStatus.COMPLETED
                await db.commit()

            except requests.exceptions.HTTPError as e:
                logger.error(f"[{source_id}] Repository API Error: {e}")
                source.status = IngestionStatus.FAILED
                source.error_message = f"Repository API Error: {e}"
                await db.commit()
            except Exception as e:
                logger.exception(f"[{source_id}] An unexpected error occurred: {e}")
                source.status = IngestionStatus.FAILED
                source.error_message = str(e)
                await db.commit()

    finally:
        logger.info(f"Cleaning up temporary directory: {temp_dir}")
        shutil.rmtree(temp_dir, ignore_errors=True)


@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_200_OK)
async def ingest_repository(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Ingests a GitHub repository asynchronously and uploads its contents to a GCS bucket.
    """
    try:
        logger.info(
            f"Received ingestion request for workspace id {request.workspace_id} for repo label: {request.source_label} and repo url: {request.source_value}"
        )

        try:
            if "github.com" in request.source_value:
                _, repo = parse_github_url(request.source_value)
            elif "gitlab.com" in request.source_value:
                _, repo = parse_gitlab_url(request.source_value)
            elif "bitbucket.org" in request.source_value:
                _, repo = parse_bitbucket_url(request.source_value)
            else:
                raise ValueError(
                    "Unsupported repository URL. Supported platforms: GitHub, GitLab, Bitbucket."
                )
        except ValueError as e:
            logger.error(f"Invalid repository URL: {e}")
            raise

        gcs_url = workspace_manager.get_workspace_path(request.workspace_id)

        # Save initial state in DB
        new_codebase_source = IngestionSource(
            id=str(f"is-{uuid.uuid4().hex[:8]}"),
            workspace_id=request.workspace_id,
            codebase_name=request.source_label,
            repo_url=request.source_value,
            gcs_destination_url=gcs_url,
            status=IngestionStatus.PENDING,
            # TODO: Update size of repository
            size=0,
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
            source_value=request.source_value,
            token=request.token,
            temp_dir=temp_dir,
            gcs_destination_path=gcs_url,
        )

        return IngestResponse(
            ws_id=request.workspace_id,
            status="success",
            message="Codebase ingestion queued successfully!",
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to create workspace: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/workspaces/{workspace_id}/source_files", response_model=list[SourceResponse]
)
async def get_sources(workspace_id: str, db: AsyncSession = Depends(get_db)):
    """Returns all ingestion sources for a given user"""
    # TODO: Implement security check to ensure user owns workspace
    # ws = workspace_manager.get_workspace(db, workspace_id, current_user.id)
    # if not ws:
    #     raise HTTPException(status_code=404, detail="Workspace not found")
    result = await db.execute(
        select(IngestionSource).filter(IngestionSource.workspace_id == workspace_id)
    )
    return result.scalars().all()


# TODO: Implement source ingestion status streaming later
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


@router.post("/verify/repo-access", response_model=VerifyRepoResponse)
async def verify_repo_access(request: VerifyRepoRequest, response: Response):
    """
    Verifies if a repository is accessible.
    """
    logger.info(f"Received verification request for URL: {request.source_value}")

    url = ""
    headers = {"Accept": "application/json"}
    auth = None

    if "github.com" in request.source_value:
        try:
            owner, repo = parse_github_url(request.source_value)
        except ValueError as e:
            logger.error(f"Invalid GitHub URL: {e}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return VerifyRepoResponse(
                status="error", message="Invalid GitHub URL", error_details=str(e)
            )
        url = f"https://api.github.com/repos/{owner}/{repo}"
        headers["Accept"] = "application/vnd.github.v3+json"
        if request.token:
            headers["Authorization"] = f"token {request.token}"

    elif "gitlab.com" in request.source_value:
        try:
            full_path, repo = parse_gitlab_url(request.source_value)
        except ValueError as e:
            logger.error(f"Invalid GitLab URL: {e}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return VerifyRepoResponse(
                status="error", message="Invalid GitLab URL", error_details=str(e)
            )
        url_encoded_path = urllib.parse.quote_plus(full_path)
        url = f"https://gitlab.com/api/v4/projects/{url_encoded_path}"
        if request.token:
            headers["PRIVATE-TOKEN"] = request.token

    elif "bitbucket.org" in request.source_value:
        try:
            workspace, repo = parse_bitbucket_url(request.source_value)
        except ValueError as e:
            logger.error(f"Invalid Bitbucket URL: {e}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return VerifyRepoResponse(
                status="error", message="Invalid Bitbucket URL", error_details=str(e)
            )
        url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo}"
        if request.token:
            headers["Authorization"] = f"Bearer {request.token}"

    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return VerifyRepoResponse(
            status="error",
            message="Unsupported repository URL. Supported platforms: GitHub, GitLab, Bitbucket.",
        )

    try:
        logger.info(f"Sending request to API: {url}")
        api_response = await run_in_threadpool(
            lambda: requests.get(url, headers=headers, auth=auth, timeout=10)
        )

        if api_response.status_code == 200:
            logger.info("Successfully verified access.")
            return VerifyRepoResponse(message="Repository is accessible.")

        logger.error(
            f"Failed to verify access: {api_response.status_code} {api_response.text}"
        )
        response.status_code = api_response.status_code

        if request.token:
            return VerifyRepoResponse(
                message="Repository access failed with the provided token.",
                error_details=api_response.text,
            )
        else:
            return VerifyRepoResponse(
                message="Repository not found or possibly private. Please try providing an access token.",
                error_details=api_response.text,
            )

    except Exception as e:
        logger.exception(
            f"Unexpected error during verification of {request.source_value}: {e}"
        )
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return VerifyRepoResponse(
            message="An unexpected error occurred during verification.",
            error_details=str(e),
        )


@router.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy"}
