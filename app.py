import os
import logging
from flask import Flask, render_template, request, redirect, session, url_for
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
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")

# Instanciar serviços
auth_service = AuthService()

# Validação de Variáveis de Ambiente Críticas
REQUIRED_ENV_VARS = ["ML_CLIENT_ID", "ML_CLIENT_SECRET", "ML_REDIRECT_URI"]
for var in REQUIRED_ENV_VARS:
    if not os.getenv(var):
        logger.warning(f"Atenção: A variável de ambiente {var} não está configurada corretamente no Render.")

@app.route("/")
def index():
    """
    Rota principal. Se autenticado, lista produtos.
    """
    access_token = session.get('access_token')
    
    # Se não houver token, renderiza página de login (o template trata isso)
    if not access_token:
        logger.info("Usuário não autenticado. Renderizando landing page.")
        return render_template("index.html", products=[])

    # Parâmetros de busca e filtro
    query = request.args.get('q', 'notebook')
    brand_filter = request.args.get('brand')

    try:
        # Busca produtos usando o serviço do ML
        ml_service = MercadoLivreService(access_token)
        products = ml_service.search_products(query=query)

        # Aplica filtro de marca se houver
        if brand_filter:
            products = ml_service.filter_by_brand(products, brand_filter)

        return render_template("index.html", products=products)
    except Exception as e:
        logger.error(f"Erro ao processar busca de produtos: {str(e)}")
        # Em caso de erro de token (401), podemos limpar a sessão e pedir novo login
        if "401" in str(e):
            session.clear()
            return redirect(url_for('index'))
        return f"Erro interno ao buscar produtos: {str(e)}", 500

@app.route("/login")
def login():
    """Redireciona para o fluxo de autorização do Mercado Livre."""
    client_id = os.getenv("ML_CLIENT_ID")
    if not client_id or client_id == "seu_client_id":
        logger.info("Credenciais não configuradas. Redirecionando para Mock.")
        return redirect(url_for('login_mock'))
    
    url = auth_service.get_auth_url()
    logger.info(f"Redirecionando para login ML: {url}")
    return redirect(url)

@app.route("/login-mock")
def login_mock():
    """Cria uma sessão fake para demonstração."""
    session['access_token'] = 'mock-token'
    return redirect(url_for('index'))

@app.route("/callback")
def callback():
    """Recebe o código do ML e troca pelo access_token."""
    code = request.args.get('code')
    error = request.args.get('error')

    if error:
        logger.error(f"Erro retornado pelo Mercado Livre no redirect: {error}")
        return f"Erro na autorização do Mercado Livre: {error}", 400

    if not code:
        logger.warning("Callback acessado sem o parâmetro 'code'.")
        return "Erro: Código de autorização não recebido do Mercado Livre.", 400
    
    try:
        logger.info(f"Iniciando troca do código pelo token. Code: {code[:10]}...")
        token_data = auth_service.exchange_code_for_token(code)
        
        if 'access_token' in token_data:
            # Salva tokens na sessão
            session['access_token'] = token_data['access_token']
            session['refresh_token'] = token_data.get('refresh_token')
            logger.info("Token obtido com sucesso. Redirecionando para index.")
            return redirect(url_for('index'))
        else:
            error_msg = token_data.get('error_description') or token_data.get('error', 'Erro desconhecido')
            logger.error(f"Erro na troca do token: {error_msg}")
            return f"Erro na autenticação: {error_msg}", 401
    except Exception as e:
        logger.error(f"Exceção fatal no processo de callback: {str(e)}")
        return f"Erro interno no processamento do login: {str(e)}", 500

@app.route("/logout")
def logout():
    """Limpa a sessão."""
    session.clear()
    return redirect(url_for('index'))

if __name__ == "__main__":
    # Garantir que a porta seja a do ambiente (Render)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
