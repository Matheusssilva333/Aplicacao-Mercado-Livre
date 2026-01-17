import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class AuthService:
    """
    Serviço responsável pela autenticação OAuth 2.0 com o Mercado Livre.
    """
    
    API_BASE_URL = "https://api.mercadolibre.com"
    AUTH_URL = "https://auth.mercadolivre.com.br/authorization"
    
    def __init__(self):
        self.client_id = os.getenv("ML_CLIENT_ID")
        self.client_secret = os.getenv("ML_CLIENT_SECRET")
        self.redirect_uri = os.getenv("ML_REDIRECT_URI")

    def get_auth_url(self):
        """Retorna a URL para o usuário iniciar a autorização."""
        return f"{self.AUTH_URL}?response_type=code&client_id={self.client_id}&redirect_uri={self.redirect_uri}"

    def exchange_code_for_token(self, code):
        """Troca o código de autorização pelo access_token."""
        url = f"{self.API_BASE_URL}/oauth/token"
        payload = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri
        }
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        
        logger.info(f"Fazendo requisição de token para {url} com redirect_uri: {self.redirect_uri}")
        response = requests.post(url, data=payload, headers=headers)
        logger.info(f"Resposta do ML: Status {response.status_code}")
        return response.json()

    def refresh_token(self, refresh_token):
        """Renova o access_token usando o refresh_token."""
        url = f"{self.API_BASE_URL}/oauth/token"
        payload = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': refresh_token
        }
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        
        response = requests.post(url, data=payload, headers=headers)
        return response.json()
