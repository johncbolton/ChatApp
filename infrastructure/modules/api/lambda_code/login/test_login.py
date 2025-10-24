import json
import pytest
from unittest.mock import patch
from botocore.exceptions import ClientError

import login


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Automatically set fake environment variables for each test."""
    monkeypatch.setenv("COGNITO_USER_POOL_ID", "fake_pool_id")
    monkeypatch.setenv("COGNITO_CLIENT_ID", "fake_client_id")


@pytest.fixture
def sample_event():
    """Base event for most POST tests."""
    return {
        "httpMethod": "POST",
        "body": json.dumps({"username": "testuser", "password": "testpass"})
    }


def test_cors_preflight():
    event = {"httpMethod": "OPTIONS"}
    result = login.lambda_handler(event, None)
    assert result["statusCode"] == 200
    assert json.loads(result["body"])["message"] == "CORS preflight OK"


def test_missing_credentials():
    event = {"httpMethod": "POST", "body": json.dumps({"username": ""})}
    result = login.lambda_handler(event, None)
    assert result["statusCode"] == 400
    assert "Invalid input" in json.loads(result["body"])["error"]


def test_invalid_json():
    event = {"httpMethod": "POST", "body": "{bad json"}
    result = login.lambda_handler(event, None)
    assert result["statusCode"] == 400
    assert "Invalid input" in json.loads(result["body"])["error"]


@patch("login.boto3.client")
def test_successful_login(mock_boto_client, sample_event):
    mock_client = mock_boto_client.return_value
    mock_client.initiate_auth.return_value = {
        "AuthenticationResult": {
            "IdToken": "fake_id_token",
            "AccessToken": "fake_access_token"
        }
    }

    result = login.lambda_handler(sample_event, None)
    body = json.loads(result["body"])

    assert result["statusCode"] == 200
    assert body["message"] == "Login successful"
    assert body["id_token"] == "fake_id_token"
    assert body["access_token"] == "fake_access_token"


@patch("login.boto3.client")
def test_not_authorized(mock_boto_client, sample_event):
    mock_client = mock_boto_client.return_value
    error_response = {"Error": {"Code": "NotAuthorizedException", "Message": "Bad credentials"}}
    mock_client.initiate_auth.side_effect = ClientError(error_response, "InitiateAuth")

    result = login.lambda_handler(sample_event, None)
    assert result["statusCode"] == 401
    assert "Invalid username or password" in json.loads(result["body"])["error"]


@patch("login.boto3.client")
def test_user_not_found(mock_boto_client, sample_event):
    mock_client = mock_boto_client.return_value
    error_response = {"Error": {"Code": "UserNotFoundException", "Message": "No such user"}}
    mock_client.initiate_auth.side_effect = ClientError(error_response, "InitiateAuth")

    result = login.lambda_handler(sample_event, None)
    assert result["statusCode"] == 404
    assert "User not found" in json.loads(result["body"])["error"]


@patch("login.boto3.client")
def test_generic_cognito_error(mock_boto_client, sample_event):
    mock_client = mock_boto_client.return_value
    error_response = {"Error": {"Code": "ServiceError", "Message": "Something went wrong"}}
    mock_client.initiate_auth.side_effect = ClientError(error_response, "InitiateAuth")

    result = login.lambda_handler(sample_event, None)
    assert result["statusCode"] == 400
    assert "Cognito error" in json.loads(result["body"])["error"]


@patch("login.boto3.client")
def test_unexpected_exception(mock_boto_client, sample_event):
    mock_client = mock_boto_client.return_value
    mock_client.initiate_auth.side_effect = RuntimeError("Boom!")

    result = login.lambda_handler(sample_event, None)
    assert result["statusCode"] == 500
    assert "unexpected error" in json.loads(result["body"])["error"].lower()

