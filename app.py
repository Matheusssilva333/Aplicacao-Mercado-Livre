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
    # Recupera tokens
    # Recupera tokens e limpa possíveis espaços em branco
    access_token = session.get('access_token') or os.getenv("ML_ACCESS_TOKEN", "")
    if access_token: access_token = access_token.strip()
    
    refresh_token = session.get('refresh_token') or os.getenv("ML_REFRESH_TOKEN", "")
    if refresh_token: refresh_token = refresh_token.strip()
    
    query = request.args.get('q', 'notebook')
    
    products = []
    error_message = None

    if access_token:
        ml_service = MercadoLivreService(access_token)
        results = ml_service.search_products(query=query)
        
        # Lógica de Diferencial: Renovação Automática
        if isinstance(results, dict) and results.get('error') == 'auth_expired' and refresh_token:
            logger.info("Access token expirado. Tentando renovação automática...")
            new_tokens = auth_service.refresh_access_token(refresh_token)
            
            if 'access_token' in new_tokens:
                access_token = new_tokens['access_token']
                session['access_token'] = access_token
                if 'refresh_token' in new_tokens:
                    session['refresh_token'] = new_tokens['refresh_token']
                
                # Tenta a busca novamente com o novo token
                ml_service = MercadoLivreService(access_token)
                results = ml_service.search_products(query=query)
            else:
                error_message = "Sua sessão expirou. Por favor, conecte sua conta novamente."
                access_token = None # Força re-login

        if isinstance(results, list):
            products = results
        elif isinstance(results, dict) and 'error' in results:
            error_message = results.get('message', "Ocorreu um erro ao buscar produtos.")
    else:
        error_message = "Conecte sua conta do Mercado Livre para realizar buscas no catálogo."

    return render_template("index.html", 
                         products=products, 
                         error_message=error_message,
                         is_logged_in=bool(access_token),
                         user_id=session.get('ml_user_id') or os.getenv("ML_USER_ID"))

@app.route("/login")
def login():
    url = auth_service.get_auth_url()
    if not url:
        logger.error("Não foi possível gerar a URL de login. Verifique as credenciais no .env")
        return redirect(url_for('index', error="config_error"))
    return redirect(url)

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
