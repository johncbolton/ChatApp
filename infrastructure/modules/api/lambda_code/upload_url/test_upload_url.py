import json
import os
import pytest
from unittest.mock import patch
import upload_url


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    # Set up environment variable for bucket
    monkeypatch.setenv("MEDIA_BUCKET_NAME", "test-bucket")
    # Reload module so env var is picked up
    import importlib
    importlib.reload(upload_url)


def test_cors_preflight():
    event = {"httpMethod": "OPTIONS"}
    response = upload_url.lambda_handler(event, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert body["message"] == "CORS preflight OK"
    assert "Access-Control-Allow-Origin" in response["headers"]


def test_successful_response():
    event = {"httpMethod": "GET"}
    response = upload_url.lambda_handler(event, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert "This is the /get-upload-url endpoint" in body["message"]
    assert body["bucket_name_from_env"] == "test-bucket"


def test_missing_env_var(monkeypatch):
    monkeypatch.delenv("MEDIA_BUCKET_NAME", raising=False)
    import importlib
    importlib.reload(upload_url)

    event = {"httpMethod": "GET"}
    response = upload_url.lambda_handler(event, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert "bucket_name_from_env" in body
    assert body["bucket_name_from_env"] is None


@patch("upload_url.s3_client")
def test_s3_client_is_initialized(mock_s3_client):
    assert hasattr(upload_url, "s3_client")
    mock_s3_client.generate_presigned_post.return_value = {
        "url": "https://example.com",
        "fields": {"key": "value"}
    }

    # You can expand this later when real S3 logic is added
    assert callable(upload_url.lambda_handler)
