import logging
import os
import tempfile
from google.cloud import storage
from google.adk.tools import ToolContext

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
