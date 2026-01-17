import os
import logging
from flask import Flask, render_template, request, redirect, session, url_for
from dotenv import load_dotenv
from services.auth import AuthService
from services.mercado_livre import MercadoLivreService

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "ml-production-key-v1")

# Inicialização segura dos serviços
auth_service = AuthService()

@app.route("/")
def index():
    access_token = session.get('access_token')
    if not access_token:
        return render_template("index.html", products=[])

    try:
        query = request.args.get('q', 'notebook')
        ml_service = MercadoLivreService(access_token)
        products = ml_service.search_products(query=query)
        
        brand_filter = request.args.get('brand')
        if brand_filter:
            products = ml_service.filter_by_brand(products, brand_filter)
            
        return render_template("index.html", products=products)
    except Exception as e:
        logger.error(f"Erro na Home: {str(e)}")
        return "Erro interno ao processar dados.", 500

@app.route("/login")
def login():
    url = auth_service.get_auth_url()
    if not url:
        return "Erro: Configuração de CLIENT_ID ou REDIRECT_URI ausente no Render.", 400
    logger.info(f"Redirecionando para login: {url}")
    return redirect(url)

@app.route("/callback")
def callback():
    code = request.args.get('code')
    error = request.args.get('error')

    if error:
        logger.error(f"Erro retornado pelo ML: {error}")
        return f"Acesso negado: {error}", 401

    if not code:
        return "Erro: Código de autorização não enviado pelo Mercado Livre.", 400

    token_data = auth_service.exchange_code_for_token(code)
    
    if 'access_token' in token_data:
        session['access_token'] = token_data['access_token']
        logger.info("Autenticação realizada com sucesso.")
        return redirect(url_for('index'))
    else:
        error_msg = token_data.get('error_description', 'Erro desconhecido')
        logger.error(f"Erro na troca do token: {error_msg}")
        return f"Falha na autenticação: {error_msg}", 401

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route("/ping")
def ping():
    return "OK", 200

if __name__ == "__main__":
    # Importante: host 0.0.0.0 e porta da variável de ambiente para o Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
