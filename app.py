import os
import logging
import sys
from flask import Flask, render_template, request, redirect, session, url_for
from dotenv import load_dotenv
from services.auth import AuthService
from services.mercado_livre import MercadoLivreService

# Configuração de Logging para nível DEBUG no Render
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("ML_PROD")

load_dotenv()

app = Flask(__name__)
# Chave de sessão persistente
app.secret_key = os.getenv("FLASK_SECRET_KEY", "ml-production-secure-key-2026")

# Inicialização do serviço com sanitização
auth_service = AuthService()

@app.before_request
def log_request_info():
    # Log de cada requisição para facilitar o debug pelo celular
    logger.info(f"Requisição: {request.method} {request.url} | User-Agent: {request.user_agent}")

@app.route("/")
def index():
    access_token = session.get('access_token')
    if not access_token:
        logger.info("Sessão vazia: Renderizando Landing Page")
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
        logger.error(f"Erro Crítico na Home: {str(e)}", exc_info=True)
        return "Erro interno ao buscar produtos. Verifique os logs do Render.", 500

@app.route("/login")
def login():
    url = auth_service.get_auth_url()
    if not url:
        logger.error("Falha ao gerar URL de Auth - Verifique ML_CLIENT_ID e ML_REDIRECT_URI")
        return "Erro de configuração no servidor.", 400
    return redirect(url)

@app.route("/callback")
def callback():
    code = request.args.get('code')
    error = request.args.get('error')

    if error:
        logger.error(f"Mercado Livre retornou erro no callback: {error}")
        return f"Erro na autorização: {error}", 401

    if not code:
        logger.warning("Callback acessado sem parâmetro 'code'")
        return "Código de autorização ausente.", 400

    token_data = auth_service.exchange_code_for_token(code)
    
    if 'access_token' in token_data:
        session['access_token'] = token_data['access_token']
        session['refresh_token'] = token_data.get('refresh_token')
        logger.info("Login OAuth2 concluído com sucesso.")
        return redirect(url_for('index'))
    else:
        error_msg = token_data.get('error_description', 'Erro na troca do token')
        logger.error(f"Falha na troca do token: {error_msg}")
        return f"Falha na autenticação: {error_msg}", 401

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route("/health")
def health():
    return {"status": "online", "domain": request.host}, 200

if __name__ == "__main__":
    # Garante que o app rode na porta do Render e aceite conexões de rede (0.0.0.0)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
