import requests

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
        Se o token for 'mock-token' ou falhar, retorna dados mockados para demonstração.
        """
        if self.access_token == "mock-token":
            return self._get_mock_products(query)

        url = f"{self.API_BASE_URL}/sites/MLB/search"
        params = {'q': query}
        
        if seller_id:
            params['seller_id'] = seller_id

        try:
            response = requests.get(url, params=params, headers=self.headers)
            if response.status_code == 401:
                return self._get_mock_products(query)
            response.raise_for_status()
            data = response.json()
            return self._normalize_results(data.get('results', []))
        except Exception as e:
            print(f"Erro ao buscar produtos: {e}. Retornando mocks.")
            return self._get_mock_products(query)

    def _get_mock_products(self, query):
        """Retorna uma lista de produtos mockados para teste."""
        mock_data = [
            {
                'id': '1', 'title': f'{query.capitalize()} Samsung Book', 'price': 3500.00,
                'currency': 'BRL', 'brand': 'Samsung', 'has_image': True,
                'thumbnail': 'https://http2.mlstatic.com/D_NQ_NP_683315-MLA44484625294_012021-V.jpg',
                'permalink': '#'
            },
            {
                'id': '2', 'title': f'{query.capitalize()} Apple MacBook Air', 'price': 8000.00,
                'currency': 'BRL', 'brand': 'Apple', 'has_image': True,
                'thumbnail': 'https://http2.mlstatic.com/D_NQ_NP_822458-MLA45231151666_032021-V.jpg',
                'permalink': '#'
            },
            {
                'id': '3', 'title': f'{query.capitalize()} Dell Inspiron', 'price': 4200.00,
                'currency': 'BRL', 'brand': 'Dell', 'has_image': True,
                'thumbnail': 'https://http2.mlstatic.com/D_NQ_NP_905291-MLA44484661073_012021-V.jpg',
                'permalink': '#'
            },
            {
                'id': '4', 'title': 'Produto sem Marca Exemplo', 'price': 150.00,
                'currency': 'BRL', 'brand': 'Marca não informada', 'has_image': True,
                'thumbnail': 'https://http2.mlstatic.com/D_NQ_NP_854515-MLA44484661073_012021-V.jpg',
                'permalink': '#'
            }
        ]
        return mock_data

    def _normalize_results(self, results):
        """
        Normaliza os dados da API para um formato mais limpo.
        Trata dados ausentes e ordena por presença de imagem.
        """
        normalized = []
        for item in results:
            # Extração segura de atributos
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
                'currency': item.get('currency_id', 'BRL'),
                'thumbnail': item.get('thumbnail', '').replace('-I.jpg', '-V.jpg'), # Melhor qualidade
                'permalink': item.get('permalink'),
                'brand': brand,
                'has_image': bool(item.get('thumbnail'))
            })

        # Ordenar: produtos com imagem primeiro
        return sorted(normalized, key=lambda x: x['has_image'], reverse=True)

    def filter_by_brand(self, products, brand_query):
        """
        Filtra uma lista de produtos por marca (case insensitive).
        """
        if not brand_query:
            return products
        
        return [
            p for p in products 
            if brand_query.lower() in p['brand'].lower()
        ]
