import os
import zipfile
import requests
from typing import Optional
from app.core.logger import get_logger

logger = get_logger(__name__)

def download_github_repo(owner: str, repo: str, dest_dir: str, token: Optional[str] = None) -> str:
    """
    Downloads the repository as a ZIP from GitHub API and extracts it.
    Returns the path to the extracted directory.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/zipball/HEAD"
    headers = {"Accept": "application/vnd.github.v3+json"}
    
    if token:
        headers["Authorization"] = f"token {token}"
        logger.info(f"Downloading {owner}/{repo} with provided token.")
    else:
        logger.info(f"Downloading {owner}/{repo} anonymously.")

    response = requests.get(url, headers=headers, stream=True)
    
    if response.status_code != 200:
        logger.error(f"Failed to download repo: {response.text}")
        response.raise_for_status()

    zip_path = os.path.join(dest_dir, f"{repo}.zip")
    with open(zip_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            
    logger.info(f"Downloaded ZIP to {zip_path}. Extracting...")
    
    extract_path = os.path.join(dest_dir, "extracted")
    os.makedirs(extract_path, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
        
    logger.info(f"Extraction complete to {extract_path}")
    
    # Typically, github zipballs extract into a single top-level folder of the format owner-repo-sha
    extracted_items = os.listdir(extract_path)
    if len(extracted_items) == 1 and os.path.isdir(os.path.join(extract_path, extracted_items[0])):
        return os.path.join(extract_path, extracted_items[0])
        
    return extract_path
