import logging
import os
import tempfile
from google.cloud import storage
from google.adk.tools import ToolContext

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String
from google.cloud import secretmanager

Base = declarative_base()

class IngestionSourceModel(Base):
    __tablename__ = "ingestion_sources"
    id = Column(String, primary_key=True)
    workspace_id = Column(String, nullable=False)
    gcs_destination_url = Column(String, nullable=False)

async def fetch_source_code_from_gcs_folder(gcs_uri: str, tool_context: ToolContext) -> bool:
    """
    Downloads the contents of a GCS folder to a temporary local directory 
    and sets the path in the tool context state.
    """
    sourceCodeStored = False
    custom_temp_path = os.getenv("CUSTOM_TEMP_PATH")
    logging.info("GCS URI => %s", gcs_uri)
    
    if not gcs_uri.startswith("gs://"):
        logging.error("Invalid GCS URI. Must start with gs://")
        return sourceCodeStored

    try:
        secure_temp_repo_dir = tempfile.mkdtemp(dir=custom_temp_path)
        logging.info("secure_temp_repo_dir => %s", secure_temp_repo_dir)

        # Parse bucket and prefix
        path_parts = gcs_uri.replace("gs://", "").split("/", 1)
        bucket_name = path_parts[0]
        prefix = path_parts[1] if len(path_parts) > 1 else ""

        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

        # Heuristic speedup: Check if a zipped archive with the same prefix name exists
        zip_blob = None
        if prefix.endswith(".zip"):
            zip_blob = bucket.blob(prefix)
        else:
            # e.g. gs://bucket/my_project/ -> check gs://bucket/my_project.zip OR check gs://bucket/my_project/.zip
            candidate_prefix = prefix.rstrip("/") + ".zip"
            if bucket.blob(candidate_prefix).exists():
                zip_blob = bucket.blob(candidate_prefix)
                logging.info("Heuristic: Found matching archive %s", candidate_prefix)

        if zip_blob and zip_blob.exists():
            logging.info("Downloading zipped archive %s for speed...", zip_blob.name)
            zip_path = os.path.join(secure_temp_repo_dir, "codebase.zip")
            zip_blob.download_to_filename(zip_path)
            
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(secure_temp_repo_dir)
            
            os.remove(zip_path)
            logging.info("Extraction complete.")
            sourceCodeStored = True
            

            
            tool_context.state["secure_temp_repo_dir"] = secure_temp_repo_dir
            return sourceCodeStored

        # Fallback to individual file downloading
        logging.info("Zipped archive not found. Falling back to listing blobs for %s", prefix)
        blobs = bucket.list_blobs(prefix=prefix)

        for blob in blobs:
            if blob.name.endswith("/"):
                continue
            
            relative_path = blob.name[len(prefix):].lstrip("/")
            file_path = os.path.join(secure_temp_repo_dir, relative_path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            blob.download_to_filename(file_path)
            logging.info("Downloaded %s to %s", blob.name, file_path)


        sourceCodeStored = True

        tool_context.state["secure_temp_repo_dir"] = secure_temp_repo_dir

    except Exception as e:
        logging.error("Exception occurred downloading from GCS: %s", e)
        return False

    return sourceCodeStored

async def _resolve_workspace_to_gcs(workspace_id: str) -> str:
    """
    Queries the database to convert workspace_id to GCS location.
    """
    logging.info("Resolving workspace ID: %s", workspace_id)
    
    try:
        db_pass = os.environ.get("INGESTION_DB_PASS")
        if not db_pass:
            raise ValueError("INGESTION_DB_PASS environment variable is not set")
        db_pass = db_pass.strip()
        
        db_user = os.environ.get("INGESTION_DB_USER", "postgres")
        db_name = os.environ.get("INGESTION_DB_NAME", "postgres")
        instance_conn_name = os.environ.get("INGESTION_INSTANCE_CONNECTION_NAME", "agents-stg:us-central1:iw-ingestion-svc-db")
        
        from urllib.parse import quote
        if os.getenv("USE_LOCAL_DB") == "true":
            uri = f"postgresql+asyncpg://{db_user}:{quote(db_pass, safe='')}@localhost:5432/{db_name}"
        else:
            uri = f"postgresql+asyncpg://{db_user}:{quote(db_pass, safe='')}@/{db_name}?host=/cloudsql/{instance_conn_name}"
        
        logging.info("Connecting to DB %s on %s as %s...", db_name, instance_conn_name, db_user)
        engine = create_async_engine(uri)
        
        async with engine.connect() as conn:
            stmt = select(IngestionSourceModel.gcs_destination_url).where(IngestionSourceModel.workspace_id == workspace_id)
            result = await conn.execute(stmt)
            gcs_url = result.scalar_one_or_none()
            
            if not gcs_url and len(workspace_id) > 11:
                prefix_id = workspace_id[:11]
                logging.info("Trying prefix match with: %s", prefix_id)
                stmt = select(IngestionSourceModel.gcs_destination_url).where(IngestionSourceModel.workspace_id == prefix_id)
                result = await conn.execute(stmt)
                gcs_url = result.scalar_one_or_none()

            if gcs_url:
                gcs_uri = gcs_url.rstrip("/")
                logging.info("Resolved workspace %s to %s", workspace_id, gcs_uri)
                return gcs_uri
            else:
                logging.warning("Workspace %s not found in ingestion_sources", workspace_id)
                return ""
                
    except Exception as e:
        logging.exception("Error resolving workspace from DB: %s", e)
        return ""
        
    finally:
        if 'engine' in locals():
            await engine.dispose()

async def resolve_workspace_gcs_uri(tool_context: ToolContext) -> str:
    """
    Resolves the GCS URI from the workspace_id stored in state.
    """
    workspace_id = tool_context.state.get("workspace_id")
    if not workspace_id:
        logging.info("No workspace_id found in state.")
        return ""
        
    gcs_uri = await _resolve_workspace_to_gcs(workspace_id)
    logging.info("Resolved workspace_id %s to %s", workspace_id, gcs_uri)
    
    return gcs_uri
