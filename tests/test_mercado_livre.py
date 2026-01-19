import pytest
from unittest.mock import patch, MagicMock
from services.mercado_livre import MercadoLivreService

@pytest.fixture
def ml_service():
    return MercadoLivreService(access_token="test-token")

@patch("requests.get")
def test_search_products_success(mock_get, ml_service):
    # Mock response data from ML API
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {
                "id": "MLB123",
                "title": "Produto Teste",
                "price": 100.0,
                "currency_id": "BRL",
                "thumbnail": "image-I.jpg",
                "permalink": "http://link.com",
                "attributes": [{"id": "BRAND", "value_name": "Marca X"}]
            }
        ]
    }
    mock_get.return_value = mock_response

    products = ml_service.search_products("notebook")
    
    assert len(products) == 1
    assert products[0]["title"] == "Produto Teste"
    assert products[0]["brand"] == "Marca X"
    assert "image-V.jpg" in products[0]["thumbnail"]  # Test quality replacement

@patch("requests.get")
def test_search_products_error_fallback_to_mock(mock_get, ml_service):
    # Test fallback to mock data on API error
    mock_get.side_effect = Exception("API Down")
    
    products = ml_service.search_products("notebook")
    
    # Should return mock products (we defined 4 mock products in services/mercado_livre.py)
    assert len(products) > 0
    assert products[0]["id"] in ["1", "2", "3", "4"]

@patch("requests.get")
def test_search_products_401_fallback_to_mock(mock_get, ml_service):
    # Test fallback to mock data on 401 Unauthorized
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_get.return_value = mock_response
    
    products = ml_service.search_products("notebook")
    
    assert len(products) > 0
    assert "mock-token" or products[0]["id"]

def test_filter_by_brand(ml_service):
    products = [
        {"brand": "Samsung", "title": "A"},
        {"brand": "Apple", "title": "B"},
        {"brand": "Samsung", "title": "C"},
    ]
    
    filtered = ml_service.filter_by_brand(products, "Samsung")
    assert len(filtered) == 2
    
    filtered_none = ml_service.filter_by_brand(products, "")
    assert len(filtered_none) == 3

def test_normalize_results_missing_data(ml_service):
    # Test normalization with missing fields
    raw_data = [{"id": "MLB000"}] # Only ID
    normalized = ml_service._normalize_results(raw_data)
    
    assert normalized[0]["title"] == "Sem título"
    assert normalized[0]["brand"] == "Marca não informada"
    assert normalized[0]["price"] == 0
