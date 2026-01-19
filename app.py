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
# Busca a chave do .env. Se não existir, gera um erro claro.
app.secret_key = os.getenv("FLASK_SECRET_KEY")
if not app.secret_key:
    logger.critical("ERRO: FLASK_SECRET_KEY não definida no arquivo .env!")

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

    if error:
        logger.error(f"Erro retornado pelo Mercado Livre no callback: {error}")
        return redirect(url_for('index', auth_error="access_denied"))

    if not code:
        logger.warning("Callback acessado sem código de autorização.")
        return redirect(url_for('index'))

    # Tenta trocar o código pelo token
    token_data = auth_service.exchange_code_for_token(code)
    
    if 'access_token' in token_data:
        # Sucesso! Armazenamos os tokens na sessão
        session['access_token'] = token_data['access_token']
        if 'refresh_token' in token_data:
            session['refresh_token'] = token_data['refresh_token']
        
        # Opcional: armazenar o user_id retornado pelo ML
        session['ml_user_id'] = token_data.get('user_id')
        
        logger.info(f"Autenticação bem-sucedida para o usuário {session['ml_user_id']}")
        return redirect(url_for('index'))
    else:
        # Falha na troca (ex: código expirado ou redirect_uri divergente)
        error_msg = token_data.get('error_description', token_data.get('message', 'Erro desconhecido'))
        logger.error(f"Falha na troca do token: {error_msg}")
        return redirect(url_for('index', auth_error=error_msg))

@app.route("/logout")
def logout():
    session.clear()
    logger.info("Sessão encerrada pelo usuário.")
    return redirect(url_for('index'))

if __name__ == "__main__":
    # Garante que temos uma secret_key configurada para as sessões funcionarem
    if not os.getenv("FLASK_SECRET_KEY"):
        logger.warning("Aviso: FLASK_SECRET_KEY não encontrada no .env. Usando chave padrão (inseguro para produção).")
        
    port = int(os.environ.get("PORT", 5000))
    # Em produção (Render), debug deve ser False
    debug_mode = os.getenv("FLASK_ENV") == "development"
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
