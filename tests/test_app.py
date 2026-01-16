import pytest
from unittest.mock import patch, MagicMock

def test_index_no_auth(client):
    """Test index page when not logged in."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Conectar Mercado Livre" in response.data

@patch("services.mercado_livre.MercadoLivreService.search_products")
def test_index_with_mock_auth(mock_search, client):
    """Test index page when logged in with mock token."""
    with client.session_transaction() as sess:
        sess['access_token'] = 'mock-token'
    
    # Mock data return
    mock_search.return_value = [{'id': '1', 'title': 'Mock Product', 'price': 100, 'brand': 'Mock', 'thumbnail': '', 'permalink': '', 'has_image': True}]
    
    response = client.get('/')
    assert response.status_code == 200
    assert b"Mock Product" in response.data
    assert b"Modo de Demonstra\xc3\xa7\xc3\xa3o" in response.data

def test_login_redirect(client):
    """Test login route redirect."""
    # With no credentials in .env, it should redirect to login-mock
    with patch("os.getenv", return_value="seu_client_id"):
        response = client.get('/login')
        assert response.status_code == 302
        assert "/login-mock" in response.headers["Location"]

def test_login_mock(client):
    """Test mock login session creation."""
    response = client.get('/login-mock')
    assert response.status_code == 302
    with client.session_transaction() as sess:
        assert sess['access_token'] == 'mock-token'

def test_logout(client):
    """Test logout clears session."""
    with client.session_transaction() as sess:
        sess['access_token'] = 'some-token'
    
    response = client.get('/logout')
    assert response.status_code == 302
    with client.session_transaction() as sess:
        assert 'access_token' not in sess

@patch("services.auth.AuthService.exchange_code_for_token")
def test_callback_success(mock_exchange, client):
    """Test successful OAuth callback."""
    mock_exchange.return_value = {"access_token": "real-token", "refresh_token": "ref-token"}
    
    response = client.get('/callback?code=valid-code')
    assert response.status_code == 302
    assert response.headers["Location"] == "/"
    
    with client.session_transaction() as sess:
        assert sess['access_token'] == 'real-token'

def test_callback_no_code(client):
    """Test callback without code parameter."""
    response = client.get('/callback')
    assert response.status_code == 400
    assert b"Erro" in response.data
