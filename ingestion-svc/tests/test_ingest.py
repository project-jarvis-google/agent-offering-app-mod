from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.utils.parsers import (
    parse_bitbucket_url,
    parse_gcs_url,
    parse_github_url,
    parse_gitlab_url,
)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health_check(client):
    response = client.get("/app-mod/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_parse_github_url_valid():
    owner, repo = parse_github_url("https://github.com/google/guava")
    assert owner == "google"
    assert repo == "guava"

    owner, repo = parse_github_url("https://github.com/kubernetes/kubernetes.git")
    assert owner == "kubernetes"
    assert repo == "kubernetes"

    owner, repo = parse_github_url("https://github.com/google/guava/tree/master")
    assert owner == "google"
    assert repo == "guava"

    owner, repo = parse_github_url("https://github.com/github-samples/pets-workshop")
    assert owner == "github-samples"
    assert repo == "pets-workshop"

    owner, repo = parse_github_url("https://github.com/github-samples/pets-workshop.git")
    assert owner == "github-samples"
    assert repo == "pets-workshop"


def test_parse_github_url_invalid():
    with pytest.raises(ValueError):
        parse_github_url("https://gitlab.com/owner/repo")


def test_parse_gitlab_url_valid():
    full_path, repo = parse_gitlab_url("https://gitlab.com/owner/repo")
    assert full_path == "owner/repo"
    assert repo == "repo"

    full_path, repo = parse_gitlab_url("https://gitlab.com/owner/subgroup/subgroup2/repo.git")
    assert full_path == "owner/subgroup/subgroup2/repo"
    assert repo == "repo"

    full_path, repo = parse_gitlab_url("https://gitlab.com/owner/subgroup/repo/-/tree/master")
    assert full_path == "owner/subgroup/repo"
    assert repo == "repo"

    full_path, repo = parse_gitlab_url(
        "https://gitlab.com/gitlab-examples/wayne-enterprises/wayne-aerospace/mission-control"
    )
    assert full_path == "gitlab-examples/wayne-enterprises/wayne-aerospace/mission-control"
    assert repo == "mission-control"

    full_path, repo = parse_gitlab_url(
        "https://gitlab.com/gitlab-examples/wayne-enterprises/wayne-aerospace/mission-control.git"
    )
    assert full_path == "gitlab-examples/wayne-enterprises/wayne-aerospace/mission-control"
    assert repo == "mission-control"


def test_parse_gitlab_url_invalid():
    with pytest.raises(ValueError):
        parse_gitlab_url("https://github.com/owner/repo")


def test_parse_bitbucket_url_valid():
    workspace, repo = parse_bitbucket_url("https://bitbucket.org/workspace/repo")
    assert workspace == "workspace"
    assert repo == "repo"

    workspace, repo = parse_bitbucket_url("https://bitbucket.org/workspace/repo.git")
    assert workspace == "workspace"
    assert repo == "repo"

    workspace, repo = parse_bitbucket_url(
        "https://bitbucket.org/atlassian_tutorial/helloworld/src/master/"
    )
    assert workspace == "atlassian_tutorial"
    assert repo == "helloworld"

    workspace, repo = parse_bitbucket_url(
        "https://bitbucket.org/atlassian_tutorial/helloworld.git"
    )
    assert workspace == "atlassian_tutorial"
    assert repo == "helloworld"


def test_parse_bitbucket_url_invalid():
    with pytest.raises(ValueError):
        parse_bitbucket_url("https://github.com/owner/repo")


def test_parse_gcs_url_valid():
    bucket, prefix = parse_gcs_url("gs://my-bucket/path/to/data")
    assert bucket == "my-bucket"
    assert prefix == "path/to/data"

    bucket, prefix = parse_gcs_url("gs://my-bucket")
    assert bucket == "my-bucket"
    assert prefix == ""


def test_parse_gcs_url_invalid():
    with pytest.raises(ValueError):
        parse_gcs_url("s3://my-bucket/path")


@patch("app.api.routes.ingest.download_github_repo")
@patch("app.api.routes.ingest.upload_directory_to_gcs")
def test_ingest_endpoint_success(mock_upload, mock_download, client):
    # Setup mocks
    mock_download.return_value = "/tmp/fake_dir"
    mock_upload.return_value = 42

    # Make request
    response = client.post(
        "/app-mod/ingest",
        json={
            "workspace_id": "ws-12345",
            "source_type": "github",
            "source_value": "https://github.com/test-owner/test-repo",
            "source_label": "test-repo",
            "token": "fake-token",
        },
    )

    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert data["ws_id"] == "ws-12345"
    assert data["status"] == "success"
    assert "queued successfully" in data["message"]

    # Assert mocks called with correct derived values
    from unittest.mock import ANY

    mock_download.assert_called_once_with("test-owner", "test-repo", ANY, "fake-token")
    mock_upload.assert_called_once_with("/tmp/fake_dir", ANY)


def test_ingest_endpoint_invalid_url(client):
    response = client.post(
        "/app-mod/ingest",
        json={
            "workspace_id": "ws-12345",
            "source_type": "github",
            "source_value": "https://invalid-url.com/repo",
            "source_label": "test-repo",
        },
    )
    assert response.status_code == 400
    assert "Repository URL does not match source type" in response.json()["detail"]


def test_ingest_endpoint_source_type_mismatch(client):
    response = client.post(
        "/app-mod/ingest",
        json={
            "workspace_id": "ws-12345",
            "source_type": "github",
            "source_value": "https://gitlab.com/owner/repo",
            "source_label": "test-repo",
        },
    )
    assert response.status_code == 400
    assert "Repository URL does not match source type" in response.json()["detail"]

