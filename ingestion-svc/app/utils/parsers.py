import re


def parse_github_url(url: str) -> tuple[str, str]:
    """Parses a GitHub URL into owner and repo, ignoring trailing browser segments."""
    pattern = r"https?://(?:www\.)?github\.com/([^/]+)/([^/]+)"
    match = re.match(pattern, url)
    if not match:
        raise ValueError(
            "Invalid GitHub URL format. Expected: https://github.com/owner/repo"
        )
    owner = match.group(1)
    repo = match.group(2)

    # Strip trailing .git if present
    if repo.endswith(".git"):
        repo = repo[:-4]

    return owner, repo


def parse_gitlab_url(url: str) -> tuple[str, str]:
    """Parses a GitLab URL into full path (owner/subgroups/repo) and repo name, ignoring trailing browser segments."""
    # Discard trailing browser segments (everything after /-/ )
    base_url = url.split("/-/", 1)[0]

    pattern = r"https?://(?:www\.)?gitlab\.com/(.+)/([^/]+)$"
    match = re.match(pattern, base_url.rstrip("/"))
    if not match:
        raise ValueError(
            "Invalid GitLab URL format. Expected: https://gitlab.com/owner/repo"
        )

    full_path = f"{match.group(1)}/{match.group(2)}"
    repo_name = match.group(2)

    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]
        if full_path.endswith(".git"):
            full_path = full_path[:-4]

    return full_path, repo_name


def parse_bitbucket_url(url: str) -> tuple[str, str]:
    """Parses a Bitbucket URL into workspace and repo, ignoring trailing browser segments."""
    pattern = r"https?://(?:www\.)?bitbucket\.org/([^/]+)/([^/]+)"
    match = re.match(pattern, url)
    if not match:
        raise ValueError(
            "Invalid Bitbucket URL format. Expected: https://bitbucket.org/workspace/repo"
        )
    workspace = match.group(1)
    repo = match.group(2)

    if repo.endswith(".git"):
        repo = repo[:-4]

    return workspace, repo


def parse_gcs_url(url: str) -> tuple[str, str]:
    """Parses a GCS URL into bucket and prefix."""
    if not url.startswith("gs://"):
        raise ValueError("Invalid GCS URL format. Expected: gs://bucket/prefix")

    parts = url[5:].split("/", 1)
    bucket = parts[0]
    prefix = parts[1] if len(parts) > 1 else ""
    return bucket, prefix

