import pytest
import os
from unittest.mock import patch, MagicMock
from services.auth import AuthService

@pytest.fixture
def auth_service():
    # Mocking environment variables
    with patch.dict(os.environ, {
        "ML_CLIENT_ID": "test_id",
        "ML_CLIENT_SECRET": "test_secret",
        "ML_REDIRECT_URI": "http://localhost:5000/callback"
    }):
        return AuthService()

def test_get_auth_url(auth_service):
    url = auth_service.get_auth_url()
    assert "response_type=code" in url
    assert "client_id=test_id" in url
    assert "redirect_uri=http://localhost:5000/callback" in url
    assert url.startswith("https://auth.mercadolivre.com.br/authorization")

@patch("requests.post")
def test_exchange_code_for_token_success(mock_post, auth_service):
    mock_response = MagicMock()
    mock_response.json.return_value = {"access_token": "mock-token", "refresh_token": "mock-refresh"}
    mock_post.return_value = mock_response

    result = auth_service.exchange_code_for_token("test-code")
    
    assert result["access_token"] == "mock-token"
    mock_post.assert_called_once()
    assert mock_post.call_args[1]['data']['code'] == "test-code"

@patch("requests.post")
def test_refresh_token_success(mock_post, auth_service):
    mock_response = MagicMock()
    mock_response.json.return_value = {"access_token": "new-token"}
    mock_post.return_value = mock_response

    result = auth_service.refresh_token("old-refresh-token")
    
    assert result["access_token"] == "new-token"
    mock_post.assert_called_once()
    assert mock_post.call_args[1]['data']['refresh_token'] == "old-refresh-token"
