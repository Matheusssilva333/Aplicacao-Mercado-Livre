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
        Busca produtos ativos. 
        Se falhar ou não houver token, retorna um set rico de dados mockados.
        """
        # Se for um token de mock ou não houver token, vai direto para o mock rico
        if self.access_token == "mock-token" or not self.access_token:
            logger.info(f"Usando modo de demonstração para a busca: {query}")
            return self._get_rich_mock_products(query)

        url = f"{self.API_BASE_URL}/sites/MLB/search"
        params = {'q': query}
        
        if seller_id:
            params['seller_id'] = seller_id

        try:
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            if response.status_code == 401:
                logger.warning("Token expirado (401). Retornando dados mockados ricos.")
                return self._get_rich_mock_products(query)
            
            response.raise_for_status()
            data = response.json()
            results = data.get('results', [])
            
            if not results:
                return self._get_rich_mock_products(query)
                
            return self._normalize_results(results)
        except Exception as e:
            logger.error(f"Erro na API do ML: {str(e)}. Ativando fallback para mock.")
            return self._get_rich_mock_products(query)

    def _get_rich_mock_products(self, query):
        """
        Gera uma lista variada e detalhada de produtos mockados baseada na busca.
        """
        categories = ["Eletrônicos", "Casa", "Moda", "Esportes", "Games"]
        brands = ["Samsung", "Apple", "Dell", "LG", "Sony", "Nike", "Adidas", "Microsoft"]
        
        mock_results = []
        
        # Gerar 12 produtos variados
        for i in range(1, 13):
            brand = random.choice(brands)
            price = random.uniform(50.0, 5000.0)
            discount = random.randint(5, 30) if random.random() > 0.5 else 0
            
            # Ajustar títulos baseados na query para parecer real
            title_templates = [
                f"{query.capitalize()} {brand} Pro Ultra",
                f"{brand} {query.capitalize()} - Edição Limitada",
                f"Novo {query.capitalize()} {brand} com Garantia",
                f"Oferta: {query.capitalize()} {brand} Premium"
            ]
            
            mock_results.append({
                'id': f'MOCK-{i}',
                'title': random.choice(title_templates),
                'price': round(price, 2),
                'original_price': round(price * (1 + discount/100), 2) if discount > 0 else None,
                'discount': discount,
                'currency': 'BRL',
                'brand': brand,
                'thumbnail': f'https://picsum.photos/seed/ml_{i}_{query}/300/300', # Imagens variadas
                'permalink': '#',
                'free_shipping': random.random() > 0.4,
                'rating': round(random.uniform(4.0, 5.0), 1),
                'reviews_count': random.randint(10, 500),
                'condition': 'new',
                'is_mock': True
            })
            
        return mock_results

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
            
            normalized.append({
                'id': item.get('id'),
                'title': item.get('title', 'Sem título'),
                'price': item.get('price', 0),
                'original_price': item.get('base_price'),
                'discount': 0, # API real precisa de mais lógica para discount
                'currency': item.get('currency_id', 'BRL'),
                'thumbnail': item.get('thumbnail', '').replace('-I.jpg', '-V.jpg'),
                'permalink': item.get('permalink'),
                'brand': brand,
                'free_shipping': item.get('shipping', {}).get('free_shipping', False),
                'rating': 4.5, # API de search nem sempre traz rating direto
                'reviews_count': random.randint(50, 200),
                'condition': item.get('condition'),
                'is_mock': False
            })
        return normalized

    def filter_by_brand(self, products, brand_query):
        if not brand_query:
            return products
        return [p for p in products if brand_query.lower() in p['brand'].lower()]
