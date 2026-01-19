import requests
import logging
import random

logger = logging.getLogger(__name__)

class MercadoLivreService:
    """
    Serviço para busca e manipulação de produtos da API do Mercado Livre.
    """
    
    API_BASE_URL = "https://api.mercadolibre.com"

    def __init__(self, access_token=None):
        self.access_token = access_token
        # Adicionando User-Agent profissional para evitar bloqueios do CloudFront/ML
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'User-Agent': 'ML-Explorer/1.0.0 (Python Flask App)',
            'Accept': 'application/json'
        } if self.access_token else {
            'User-Agent': 'ML-Explorer/1.0.0 (Python Flask App)',
            'Accept': 'application/json'
        }

    def search_products(self, query="notebook", seller_id=None):
        """
        Busca produtos ativos usando a API real.
        Tenta modo autenticado primeiro, depois modo público em caso de erro.
        """
        url = f"{self.API_BASE_URL}/sites/MLB/search"
        params = {'q': query}
        if seller_id:
            params['seller_id'] = seller_id

        # Tentativa 1: Com Token (se existir)
        if self.access_token:
            try:
                logger.info(f"Tentando busca autenticada para: {query}")
                response = requests.get(url, params=params, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    return self._normalize_results(response.json().get('results', []))
                else:
                    logger.warning(f"Busca autenticada falhou ({response.status_code}). Tentando modo público...")
            except Exception as e:
                logger.error(f"Erro na busca autenticada: {e}")

        # Tentativa 2: Modo Público (sem token) - Evita o erro 403 do CloudFront
        try:
            logger.info(f"Executando busca pública para: {query}")
            public_headers = {'User-Agent': 'ML-Explorer/1.0.0 (Python Flask App)'}
            response = requests.get(url, params=params, headers=public_headers, timeout=10)
            response.raise_for_status()
            return self._normalize_results(response.json().get('results', []))
        except Exception as e:
            logger.error(f"Erro fatal na busca pública: {str(e)}")
            return []

    def _normalize_results(self, results):
        """Normaliza os dados da API real."""
        normalized = []
        for item in results:
            attributes = item.get('attributes', [])
            brand = "Marca não informada"
            for attr in attributes:
                if attr.get('id') == 'BRAND':
                    brand = attr.get('value_name', brand)
                    break
            
            # Ajuste da imagem para maior qualidade
            thumbnail = item.get('thumbnail', '')
            if thumbnail.endswith('-I.jpg'):
                thumbnail = thumbnail.replace('-I.jpg', '-V.jpg')
            
            normalized.append({
                'id': item.get('id'),
                'title': item.get('title', 'Sem título'),
                'price': item.get('price', 0),
                'original_price': item.get('base_price'),
                'discount': 0, # Cálculo de desconto pode ser adicionado aqui
                'currency': item.get('currency_id', 'BRL'),
                'thumbnail': thumbnail,
                'permalink': item.get('permalink'),
                'brand': brand,
                'free_shipping': item.get('shipping', {}).get('free_shipping', False),
                'rating': item.get('reviews', {}).get('rating_average', 4.5), # Fallback caso não venha
                'reviews_count': item.get('reviews', {}).get('total', 0),
                'condition': item.get('condition'),
                'is_mock': False
            })
        return normalized

    def filter_by_brand(self, products, brand_query):
        if not brand_query:
            return products
        return [p for p in products if brand_query.lower() in p['brand'].lower()]
