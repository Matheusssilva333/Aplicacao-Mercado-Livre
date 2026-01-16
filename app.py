import os
from flask import Flask, render_template, request, redirect, session, url_for
from dotenv import load_dotenv
from services.auth import AuthService
from services.mercado_livre import MercadoLivreService


# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")

# Instanciar serviços
auth_service = AuthService()

@app.route("/")
def index():
    """
    Rota principal. Se autenticado, lista produtos.
    """
    access_token = session.get('access_token')
    
    # Se não houver token, renderiza página de login (o template trata isso)
    if not access_token:
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

@app.route("/login")
def login():
    """Redireciona para o fluxo de autorização do Mercado Livre."""
    # Se não houver credenciais reais, avisa ou redireciona para mock
    client_id = os.getenv("ML_CLIENT_ID")
    if not client_id or client_id == "seu_client_id":
        return redirect(url_for('login_mock'))
    return redirect(auth_service.get_auth_url())

@app.route("/login-mock")
def login_mock():
    """Cria uma sessão fake para demonstração."""
    session['access_token'] = 'mock-token'
    return redirect(url_for('index'))

@app.route("/callback")
def callback():
    """Recebe o código do ML e troca pelo access_token."""
    code = request.args.get('code')
    if not code:
        return "Erro: Código de autorização não recebido.", 400
    
    token_data = auth_service.exchange_code_for_token(code)
    
    if 'access_token' in token_data:
        # Salva tokens na sessão (em produção use um banco de dados)
        session['access_token'] = token_data['access_token']
        session['refresh_token'] = token_data.get('refresh_token')
        return redirect(url_for('index'))
    else:
        return f"Erro na autenticação: {token_data.get('error_description', 'Erro desconhecido')}", 401

@app.route("/logout")
def logout():
    """Limpa a sessão."""
    session.clear()
    return redirect(url_for('index'))

if __name__ == "__main__":
    # Rodar em modo debug para desenvolvimento
    # A URL de callback no painel do ML deve bater com esta porta
    app.run(debug=True, port=5000)
