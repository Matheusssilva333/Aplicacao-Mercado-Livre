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
        self.headers = {
            'Authorization': f'Bearer {self.access_token}'
        } if self.access_token else {}

    def search_products(self, query="notebook", seller_id=None):
        """
        Busca produtos ativos usando a API real.
        Exige um token de acesso válido.
        """
        if not self.access_token:
            logger.error("Tentativa de busca sem token de acesso.")
            return []

        url = f"{self.API_BASE_URL}/sites/MLB/search"
        params = {'q': query}
        
        if seller_id:
            params['seller_id'] = seller_id

        try:
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            
            if response.status_code == 401:
                logger.warning("Token expirado ou inválido (401).")
                return []
            
            response.raise_for_status()
            data = response.json()
            results = data.get('results', [])
            
            return self._normalize_results(results)
        except Exception as e:
            logger.error(f"Erro na API do ML: {str(e)}")
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
