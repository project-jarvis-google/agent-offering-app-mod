from fastapi.testclient import TestClient
from app.main import app
from app.utils.parsers import parse_github_url, parse_gcs_url
import pytest
from unittest.mock import patch, MagicMock

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_parse_github_url_valid():
    owner, repo = parse_github_url("https://github.com/google/guava")
    assert owner == "google"
    assert repo == "guava"

    owner, repo = parse_github_url("https://github.com/kubernetes/kubernetes.git")
    assert owner == "kubernetes"
    assert repo == "kubernetes"
    
def test_parse_github_url_invalid():
    with pytest.raises(ValueError):
        parse_github_url("https://gitlab.com/owner/repo")

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
def test_ingest_endpoint_success(mock_upload, mock_download):
    # Setup mocks
    mock_download.return_value = "/tmp/fake_dir"
    mock_upload.return_value = 42

    # Make request
    response = client.post(
        "/ingest",
        json={
            "repo_url": "https://github.com/test-owner/test-repo",
            "gcs_url": "gs://test-bucket/test-prefix",
            "token": "fake-token"
        }
    )

    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["files_uploaded"] == 42
    
    # Assert mocks called with correct derived values
    from unittest.mock import ANY
    mock_download.assert_called_once_with("test-owner", "test-repo", ANY, "fake-token")
    mock_upload.assert_called_once_with("/tmp/fake_dir", "gs://test-bucket/test-prefix")

def test_ingest_endpoint_invalid_github_url():
    response = client.post(
        "/ingest",
        json={
            "repo_url": "https://invalid-url.com/repo",
            "gcs_url": "gs://test-bucket/test-prefix"
        }
    )
    assert response.status_code == 400
    assert "Invalid GitHub URL" in response.json()["detail"]

def test_ingest_endpoint_invalid_gcs_url():
    response = client.post(
        "/ingest",
        json={
            "repo_url": "https://github.com/owner/repo",
            "gcs_url": "invalid-gcs-url/prefix"
        }
    )
    assert response.status_code == 400
    assert "Invalid GCS URL" in response.json()["detail"]
