import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_exchange():
    client_id = os.getenv("ML_CLIENT_ID")
    client_secret = os.getenv("ML_CLIENT_SECRET")
    redirect_uri = os.getenv("ML_REDIRECT_URI")
    code = "TG-696e6642b9b2e70001ef50ad-2555606621" # Código fornecido pelo usuário

    url = "https://api.mercadolibre.com/oauth/token"
    payload = {
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code.strip(),
        'redirect_uri': redirect_uri
    }
    
    headers = {
        'accept': 'application/json',
        'content-type': 'application/x-www-form-urlencoded'
    }

    print(f"--- Testando Troca de Token ---")
    print(f"Client ID: {client_id}")
    print(f"Redirect URI: {redirect_uri}")
    print(f"Code: {code[:15]}...")
    
    response = requests.post(url, data=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Resposta: {response.text}")

if __name__ == "__main__":
    test_exchange()
