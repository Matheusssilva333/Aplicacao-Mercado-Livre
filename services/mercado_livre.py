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
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'User-Agent': 'ML-Explorer/1.0.0'
        }

    def search_products(self, query="notebook"):
        """
        Busca produtos ativos no catálogo usando o endpoint obrigatório do desafio.
        """
        if not self.access_token:
            logger.warning("Tentativa de busca sem access_token.")
            return []

        # Endpoint específico solicitado no desafio
        url = f"{self.API_BASE_URL}/products/search"
        
        # Parâmetros mínimos exigidos
        params = {
            'status': 'active',
            'site_id': 'MLB',
            'q': query,
            'limit': 10
        }

        try:
            logger.info(f"Buscando no catálogo: {query}")
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            
            if response.status_code == 401:
                logger.error("Token expirado ou inválido (401)")
                return {"error": "auth_expired"}
                
            response.raise_for_status()
            data = response.json()
            
            # O endpoint /products/search pode retornar 'results' ou 'products' dependendo da versão
            results = data.get('results', [])
            
            normalized = self._normalize_results(results)
            
            # Requisito 4: Ordenação (Produtos com imagem primeiro)
            normalized.sort(key=lambda x: x['has_image'], reverse=True)
            
            return normalized
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Erro HTTP na API ML: {e}")
            try:
                error_detail = response.json().get('message') or response.json().get('error')
            except:
                error_detail = response.text
            return {"error": "api_error", "message": f"Erro na API ({response.status_code}): {error_detail}"}
        except Exception as e:
            logger.error(f"Erro inesperado na busca: {str(e)}")
            return []

    def _normalize_results(self, results):
        """Normaliza os dados seguindo os requisitos do desafio."""
        normalized = []
        for item in results:
            # Captura atributos (exige pelo menos 3)
            raw_attributes = item.get('attributes', [])
            attrs_dict = {attr.get('id'): attr.get('value_name') for attr in raw_attributes if attr.get('value_name')}
            
            # Atributos específicos solicitados no desafio ou relevantes
            display_attrs = []
            
            # Tenta pegar Marca, Cor e um terceiro (Capacidade ou Modelo)
            brand = attrs_dict.get('BRAND', attrs_dict.get('MARCA', 'Não informado'))
            color = attrs_dict.get('COLOR', attrs_dict.get('COR', 'Não informado'))
            
            # Terceiro atributo dinâmico (Capacidade, Modelo ou o primeiro disponível que não seja marca/cor)
            model = attrs_dict.get('MODEL', attrs_dict.get('MODELO'))
            capacity = attrs_dict.get('CAPACITY', attrs_dict.get('CAPACIDADE'))
            third_attr = capacity or model or "Não informado"
            
            # Se ainda faltar, pega qualquer outro disponível
            if third_attr == "Não informado":
                for k, v in attrs_dict.items():
                    if k not in ['BRAND', 'MARCA', 'COLOR', 'COR'] and v:
                        third_attr = v
                        break

            # Imagem e Placeholder
            thumbnail = item.get('thumbnail', '')
            has_image = bool(thumbnail and "placeholder" not in thumbnail.lower())
            
            # Melhorar qualidade da imagem se possível
            if has_image and thumbnail.endswith('-I.jpg'):
                thumbnail = thumbnail.replace('-I.jpg', '-V.jpg')

            normalized.append({
                'id': item.get('id'),
                'title': item.get('name', item.get('title', 'Sem título')), # /products usa 'name'
                'status': 'Ativo' if item.get('status') == 'active' else item.get('status', 'Inativo'),
                'price': item.get('price', 0),
                'thumbnail': thumbnail if has_image else "https://via.placeholder.com/300x300?text=Sem+Imagem",
                'has_image': has_image,
                'permalink': item.get('permalink', '#'),
                'brand': brand,
                'color': color,
                'additional_attr': third_attr,
                'attributes': [
                    {'label': 'Marca', 'value': brand},
                    {'label': 'Cor', 'value': color},
                    {'label': 'Capacidade/Modelo', 'value': third_attr}
                ]
            })
        return normalized

    def filter_by_brand(self, products, brand_query):
        if not brand_query:
            return products
        return [p for p in products if brand_query.lower() in p['brand'].lower()]
