import os
import logging
import traceback
from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from dotenv import load_dotenv
from services.auth import AuthService
from services.mercado_livre import MercadoLivreService

# Configuração de Logging para Produção
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
# Chave de sessão é obrigatória para usar session
app.secret_key = os.getenv("FLASK_SECRET_KEY", "ml-agent-default-key-123")

# Instanciar serviços fora do bloco __main__ para que o Gunicorn os veja
try:
    auth_service = AuthService()
    logger.info("AuthService inicializado com sucesso.")
except Exception as e:
    logger.error(f"Erro ao inicializar AuthService: {str(e)}")

@app.errorhandler(500)
def internal_error(error):
    """Captura erros 500 e exibe o traceback para debug (apenas em desenvolvimento/debug)."""
    err_msg = traceback.format_exc()
    logger.error(f"Erro 500 Detectado: {err_msg}")
    # Em produção real, você não exibiria o traceback, mas para debug no Render é essencial agora
    return f"<h1>Erro 500 - Detalhes do Erro</h1><pre>{err_msg}</pre>", 500

@app.route("/ping")
def ping():
    return "pong", 200

@app.route("/")
def index():
    """
    Rota principal. Se autenticado, lista produtos.
    """
    try:
        access_token = session.get('access_token')
        
        # Se não houver token, renderiza página de login
        if not access_token:
            logger.info("Usuário não autenticado. Renderizando landing page.")
            return render_template("index.html", products=[])

        # Parâmetros de busca e filtro
        query = request.args.get('q', 'notebook')
        brand_filter = request.args.get('brand')

        # Busca produtos usando o serviço do ML
        ml_service = MercadoLivreService(access_token)
        products = ml_service.search_products(query=query)

        # Aplica filtro de marca se houver
        if brand_filter:
            products = ml_service.filter_by_brand(products, brand_filter)

        return render_template("index.html", products=products)
    except Exception as e:
        err_msg = traceback.format_exc()
        logger.error(f"Erro na rota /: {err_msg}")
        return f"Erro ao carregar página principal: <pre>{err_msg}</pre>", 500

@app.route("/login")
def login():
    """Redireciona para o fluxo de autorização do Mercado Livre."""
    try:
        client_id = os.getenv("ML_CLIENT_ID")
        if not client_id or client_id == "seu_client_id" or client_id == "":
            logger.info("ML_CLIENT_ID não configurado. Redirecionando para Mock.")
            return redirect(url_for('login_mock'))
        
        url = auth_service.get_auth_url()
        logger.info(f"Redirecionando para: {url}")
        return redirect(url)
    except Exception as e:
        err_msg = traceback.format_exc()
        logger.error(f"Erro na rota /login: {err_msg}")
        return f"Erro ao iniciar login: <pre>{err_msg}</pre>", 500

@app.route("/login-mock")
def login_mock():
    """Cria uma sessão fake para demonstração."""
    session['access_token'] = 'mock-token'
    return redirect(url_for('index'))

@app.route("/callback")
def callback():
    """Recebe o código do ML e troca pelo access_token."""
    try:
        code = request.args.get('code')
        error = request.args.get('error')

        if error:
            logger.error(f"Erro do ML no Callback: {error}")
            return f"Erro na autorização do Mercado Livre: {error}", 400

        if not code:
            logger.warning("Callback acessado sem 'code'.")
            return "Erro: Código de autorização não recebido.", 400
        
        logger.info(f"Processando callback para o código: {code[:10]}...")
        token_data = auth_service.exchange_code_for_token(code)
        
        if 'access_token' in token_data:
            session['access_token'] = token_data['access_token']
            session['refresh_token'] = token_data.get('refresh_token')
            logger.info("Login realizado com sucesso.")
            return redirect(url_for('index'))
        else:
            error_msg = token_data.get('error_description') or token_data.get('error', 'Erro desconhecido')
            logger.error(f"Erro ao trocar token: {error_msg}")
            return f"Erro na autenticação: {error_msg}", 401
    except Exception as e:
        err_msg = traceback.format_exc()
        logger.error(f"Erro na rota /callback: {err_msg}")
        return f"Erro no processamento do callback: <pre>{err_msg}</pre>", 500

@app.route("/logout")
def logout():
    """Limpa a sessão."""
    session.clear()
    return redirect(url_for('index'))

if __name__ == "__main__":
    # Garantir que a porta seja a do ambiente (Render)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
