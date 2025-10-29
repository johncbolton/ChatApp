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


from botocore.exceptions import ClientError


@patch("upload_url.s3_client")
def test_successful_response(mock_s3_client):
    mock_s3_client.generate_presigned_post.return_value = {
        "url": "https://test-bucket.s3.amazonaws.com/",
        "fields": {"key": "uploads/some-uuid"}
    }

    event = {"httpMethod": "GET"}
    response = upload_url.lambda_handler(event, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert "url" in body
    assert "fields" in body
    assert "key" in body["fields"]
    mock_s3_client.generate_presigned_post.assert_called_once()


def test_missing_env_var(monkeypatch):
    monkeypatch.delenv("MEDIA_BUCKET_NAME", raising=False)
    import importlib
    importlib.reload(upload_url)

    event = {"httpMethod": "GET"}
    response = upload_url.lambda_handler(event, None)
    body = json.loads(response["body"])


    assert response["statusCode"] == 500
    assert "MEDIA_BUCKET_NAME" in body["message"]

@patch("upload_url.s3_client")
def test_s3_client_error(mock_s3_client):
    mock_s3_client.generate_presigned_post.side_effect = ClientError(
        {"Error": {"Code": "InternalError", "Message": "An internal error occurred"}},
        "GeneratePresignedPost"
    )

    event = {"httpMethod": "GET"}
    response = upload_url.lambda_handler(event, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 500
    assert "Could not generate an upload URL" in body["message"]
