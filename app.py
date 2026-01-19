import os
import logging
import sys
from flask import Flask, render_template, request, redirect, session, url_for
from dotenv import load_dotenv
from services.auth import AuthService
from services.mercado_livre import MercadoLivreService

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("ML_PROD")

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "ml-production-secure-key-2026")

auth_service = AuthService()

@app.route("/")
def index():
    access_token = session.get('access_token')
    query = request.args.get('q', 'notebook')
    brand_filter = request.args.get('brand')
    
    # Instancia serviço (mesmo sem token para permitir modo Mock rico)
    ml_service = MercadoLivreService(access_token)
    
    try:
        # Tenta buscar produtos (o serviço já lida com o fallback para mock rico internamente)
        products = ml_service.search_products(query=query)
        
        if brand_filter:
            products = ml_service.filter_by_brand(products, brand_filter)
            
        return render_template("index.html", products=products, is_logged_in=bool(access_token))
    except Exception as e:
        logger.error(f"Erro fatal na rota principal: {str(e)}")
        # Última linha de defesa: Mock forçado
        products = ml_service._get_rich_mock_products(query)
        return render_template("index.html", products=products, is_logged_in=bool(access_token))

@app.route("/login")
def login():
    url = auth_service.get_auth_url()
    if not url:
        return redirect(url_for('login_mock'))
    return redirect(url)

@app.route("/login-mock")
def login_mock():
    session['access_token'] = 'mock-token'
    return redirect(url_for('index'))

@app.route("/callback")
def callback():
    code = request.args.get('code')
    error = request.args.get('error')

    if error or not code:
        logger.warning(f"Falha no callback: {error or 'sem código'}")
        return redirect(url_for('index'))

    token_data = auth_service.exchange_code_for_token(code)
    print("token_data", token_data)
    if 'access_token' in token_data:
        session['access_token'] = token_data['access_token']
        logger.info("Autenticação realizada com sucesso.")
        return redirect(url_for('index'))
    else:
        logger.error(f"Erro na troca do token: {token_data.get('error_description')}")
        return redirect(url_for('index'))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)