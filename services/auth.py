------++import requests
import os
import logging
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class AuthService:
    """
    Serviço oficial para fluxo Authorization Code do Mercado Livre.
    """
    API_BASE_URL = "https://api.mercadolibre.com"
    # Usando o domínio global para maior compatibilidade
    AUTH_URL = "https://auth.mercadolivre.com.br/authorization"
    
    def __init__(self):
        # Sanitização: remove espaços e quebras de linha acidentais
        self.client_id = str(os.getenv("ML_CLIENT_ID", "")).strip()
        self.client_secret = str(os.getenv("ML_CLIENT_SECRET", "")).strip()
        self.redirect_uri = str(os.getenv("ML_REDIRECT_URI", "")).strip()

    def get_auth_url(self):
        """Gera URL de autorização com encoding correto."""
        if not self.client_id or not self.redirect_uri:++-
            logger.error("Configurações ML_CLIENT_ID ou ML_REDIRECT_URI ausentes no .env")
            return None
            
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "offline_access read"
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

    def exchange_code_for_token(self, code):
        """Troca o 'code' pelo token real."""
        url = f"{self.API_BASE_URL}/oauth/token"
        
        # O ML exige que o redirect_uri seja idêntico ao usado no get_auth_url
        payload = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code.strip(),
            'redirect_uri': self.redirect_uri
        }
        
        headers = {
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'User-Agent': 'ML-Explorer/1.0.0 (Python Flask App)'
        }
        
        try:
            logger.info(f"Iniciando troca de token para o código: {code[:10]}...")
            response = requests.post(url, data=payload, headers=headers, timeout=15)
            
            if response.status_code != 200:
                logger.error(f"Erro na API ML ({response.status_code}): {response.text}")
                return response.json()
                
            return response.json()
        except Exception as e:
            logger.error(f"Erro de conexão com Mercado Livre: {str(e)}")
            return {"error": "connection_error", "message": str(e)}

    def refresh_access_token(self, refresh_token):
        """Usa o refresh_token para obter um novo access_token."""
        url = f"{self.API_BASE_URL}/oauth/token"
        
        payload = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': refresh_token.strip()
        }
        
        headers = {
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded'
        }
        
        try:
            logger.info("Tentando renovar o token de acesso...")
            response = requests.post(url, data=payload, headers=headers, timeout=15)
            return response.json()
        except Exception as e:
            logger.error(f"Erro ao renovar token: {str(e)}")
            return {"error": "connection_error", "message": str(e)}
