import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class AuthService:
    """
    Serviço oficial para fluxo Authorization Code do Mercado Livre.
    """
    API_BASE_URL = "https://api.mercadolibre.com"
    AUTH_URL = "https://auth.mercadolivre.com.br/authorization"
    
    def __init__(self):
        # Sanitização agressiva: remove quebras de linha e espaços invisíveis
        self.client_id = str(os.getenv("ML_CLIENT_ID", "")).strip().replace("\n", "").replace("\r", "")
        self.client_secret = str(os.getenv("ML_CLIENT_SECRET", "")).strip().replace("\n", "").replace("\r", "")
        self.redirect_uri = str(os.getenv("ML_REDIRECT_URI", "")).strip().replace("\n", "").replace("\r", "")

    def get_auth_url(self):
        """Gera URL de autorização baseada na documentação oficial."""
        if not self.client_id or not self.redirect_uri:
            logger.error("Configuração ausente: client_id ou redirect_uri")
            return None
            
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri
        }
        # Montagem manual para garantir que não haja caracteres de escape extras
        query = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.AUTH_URL}?{query}"

    def exchange_code_for_token(self, code):
        """Troca o 'code' pelo token conforme documentação oficial."""
        url = f"{self.API_BASE_URL}/oauth/token"
        payload = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code.strip(),
            'redirect_uri': self.redirect_uri
        }
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        
        try:
            logger.info(f"Requisitando token. URL: {url} | Redirect URI: {self.redirect_uri}")
            response = requests.post(url, data=payload, headers=headers, timeout=15)
            return response.json()
        except Exception as e:
            logger.error(f"Falha na comunicação com API ML: {str(e)}")
            return {"error": "connection_error", "error_description": str(e)}
