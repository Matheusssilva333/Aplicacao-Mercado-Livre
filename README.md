# Catálogo de Produtos Mercado Livre - Desafio Técnico

Este projeto é uma aplicação Flask desenvolvida para o desafio de integração com a API do Mercado Livre. A aplicação permite buscar produtos ativos no catálogo, exibindo-os em cards detalhados com atributos específicos e suporte a autenticação OAuth 2.0.

## 🚀 Funcionalidades

- **Busca no Catálogo**: Consulta o endpoint oficial `/products/search` com limites e filtros obrigatórios (`status=active`).
- **Autenticação OAuth 2.0**: Fluxo completo de autorização obrigatório para acesso aos dados.
- **Diferencial - Renovação Automática**: Implementação de lógica para renovar o `access_token` automaticamente usando o `refresh_token` sem interromper a experiência do usuário.
- **Tratamento de Dados**: Normalização robusta de atributos (Marca, Cor, Modelo/Capacidade) com fallback para "Não informado".
- **Ordenação Inteligente**: Exibição prioritária de produtos que possuem imagens reais.
- **Interface Premium**: Design responsivo inspirado no sistema visual do Mercado Livre, utilizando Vanilla CSS.

## 📂 Estrutura do Projeto

- `app.py`: Servidor Flask e gerenciamento de rotas/sessão.
- `services/auth.py`: Serviço especializado na gestão de tokens e fluxo OAuth.
- `services/mercado_livre.py`: Abstração para chamadas à API e normalização de dados.
- `templates/`: Interface Jinja2 com foco em experiência do usuário.
- `static/styles.css`: Design system personalizado.

## 🛠️ Como Rodar o Projeto

### 1. Pré-requisitos
- Python 3.10+
- Credenciais de uma aplicação criada no [ML Dev Center](https://developers.mercadolivre.com.br/dev-center/).

### 2. Configuração do ambiente
```bash
# Clone o repositório
git clone <url-do-repo>
cd aplicacao-mercado-livre

# Instale as dependências
pip install -r requirements.txt
```

### 3. Configuração das Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto com as seguintes chaves:
```text
ML_CLIENT_ID=seu_id
ML_CLIENT_SECRET=sua_secret
ML_REDIRECT_URI=http://localhost:5000/callback
FLASK_SECRET_KEY=sua_chave_secreta_flask
```

### 4. Execução
```bash
python app.py
```
Acesse `http://localhost:5000`.

## 📘 Decisões Técnicas

- **Separação de Camadas**: A lógica de API foi isolada em `services/` para manter o `app.py` limpo e focado em roteamento.
- **Resiliência**: Foi implementada uma lógica de retry no backend. Se uma busca falha por token expirado (401), o sistema tenta renovar o token e repetir a busca silenciosamente.
- **Experiência do Usuário**: Erros técnicos são capturados e transformados em mensagens amigáveis na interface, evitando a exibição de stack traces.
- **Dados do Catálogo**: O endpoint `/products/search` foi escolhido conforme exigido no desafio, garantindo que os resultados venham do catálogo oficial de produtos.

---
Desenvolvido por [Antigravity/User] como parte de um desafio técnico.
