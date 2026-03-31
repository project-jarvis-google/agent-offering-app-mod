import re

def parse_github_url(url: str) -> tuple[str, str]:
    """Parses a GitHub URL into owner and repo."""
    # Matches https://github.com/owner/repo or https://github.com/owner/repo.git
    pattern = r"https?://github\.com/([^/]+)/([^/.]+?)(?:\.git|/)?$"
    match = re.search(pattern, url)
    if not match:
        raise ValueError("Invalid GitHub URL format. Expected: https://github.com/owner/repo")
    return match.group(1), match.group(2)

def parse_gcs_url(url: str) -> tuple[str, str]:
    """Parses a GCS URL into bucket and prefix."""
    if not url.startswith("gs://"):
        raise ValueError("Invalid GCS URL format. Expected: gs://bucket/prefix")
    
    parts = url[5:].split("/", 1)
    bucket = parts[0]
    prefix = parts[1] if len(parts) > 1 else ""
    return bucket, prefix
