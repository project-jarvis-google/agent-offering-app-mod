import os
import urllib.parse
import zipfile

import requests

from app.core.logger import get_logger

logger = get_logger(__name__)


def download_gitlab_repo(
    full_path: str, repo: str, dest_dir: str, token: str | None = None
) -> str:
    """
    Downloads the GitLab repository as a ZIP from GitLab API and extracts it.
    Returns the path to the extracted directory.
    """
    url_encoded_path = urllib.parse.quote_plus(full_path)
    url = f"https://gitlab.com/api/v4/projects/{url_encoded_path}/repository/archive.zip"
    headers = {"Accept": "application/json"}

    if token:
        # Use the standard header for GitLab Personal Access Tokens (PAT)
        headers["PRIVATE-TOKEN"] = token
        logger.info(f"Downloading GitLab repo {full_path} with provided PAT.")
    else:
        logger.info(f"Downloading GitLab repo {full_path} anonymously.")

    response = requests.get(url, headers=headers, stream=True)

    if response.status_code != 200:
        logger.error(f"Failed to download GitLab repo: {response.text}")
        response.raise_for_status()

    zip_path = os.path.join(dest_dir, f"{repo}.zip")
    with open(zip_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    logger.info(f"Downloaded ZIP to {zip_path}. Extracting...")

    extract_path = os.path.join(dest_dir, "extracted")
    os.makedirs(extract_path, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)

    logger.info(f"Extraction complete to {extract_path}")

    # GitLab zipballs typically extract into a single top-level folder of the format owner-repo-sha
    extracted_items = os.listdir(extract_path)
    if len(extracted_items) == 1 and os.path.isdir(
        os.path.join(extract_path, extracted_items[0])
    ):
        return os.path.join(extract_path, extracted_items[0])

    return extract_path
