import os
import concurrent.futures
from google.cloud import storage
from app.core.logger import get_logger
from app.utils.parsers import parse_gcs_url

logger = get_logger(__name__)

def _upload_single_file(local_path: str, bucket_name: str, gcs_blob_name: str) -> None:
    try:
        # We instantiate a client per thread to be safe, though according to docs the client is primarily stateless thread-safe
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(gcs_blob_name)
        blob.upload_from_filename(local_path)
        logger.debug(f"Uploaded {local_path} to gs://{bucket_name}/{gcs_blob_name}")
    except Exception as e:
        logger.error(f"Failed to upload {local_path} to {gcs_blob_name}: {e}")
        raise

def upload_directory_to_gcs(local_dir: str, gcs_destination_path: str, max_workers: int = 10) -> int:
    """
    Uploads a directory concurrently to a given GCS bucket and prefix.
    Returns the number of files uploaded.
    """
    try:
        bucket_name, prefix = parse_gcs_url(gcs_destination_path)
    except ValueError as e:
        logger.error(f"Invalid GCS URL {gcs_destination_path}: {e}")
        raise

    logger.info(f"Starting upload of {local_dir} to gs://{bucket_name}/{prefix} using {max_workers} workers.")
    
    upload_tasks = []
    
    # Pre-calculate files to upload
    for root, _, files in os.walk(local_dir):
        for file in files:
            local_path = os.path.join(root, file)
            # Calculate the relative path from the root of local_dir to preserve structure
            relative_path = os.path.relpath(local_path, local_dir)
            gcs_blob_name = os.path.join(prefix, relative_path).replace("\\", "/") # Normalize for windows paths just in case
            # Remove leading slashes from blob name if any
            if gcs_blob_name.startswith('/'):
                gcs_blob_name = gcs_blob_name[1:]
                
            upload_tasks.append((local_path, bucket_name, gcs_blob_name))
            
    if not upload_tasks:
        logger.warning(f"No files found in {local_dir}")
        return 0
        
    logger.info(f"Found {len(upload_tasks)} files to upload.")

    success_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_task = {
            executor.submit(_upload_single_file, path, bkt, blb): (path, blb) 
            for path, bkt, blb in upload_tasks
        }
        
        for future in concurrent.futures.as_completed(future_to_task):
            path, blb = future_to_task[future]
            try:
                future.result()
                success_count += 1
                logger.info(f"success_count => {success_count}")
            except Exception as e:
                logger.error(f"Error executing upload task for {blb}: {e}")

    logger.info(f"Successfully uploaded {success_count}/{len(upload_tasks)} files to gs://{bucket_name}/{prefix}")
    return success_count
