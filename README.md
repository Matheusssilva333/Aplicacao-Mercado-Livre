# Aplicação Integrada ao Mercado Livre

Este projeto é uma aplicação de busca de produtos integrada à API do Mercado Livre com testes automatizados e com a biblioteca de segurança DOMpurify para um desafio de entrada em um projeto.

## 🚀 Funcionalidades

- **Autenticação OAuth 2.0**: Fluxo completo de autorização e obtenção de token.
- **Busca de Produtos**: Integração com o endpoint de busca do Mercado Livre.
- **Normalização de Dados**: Limpeza e tratamento dos dados retornados pela API.
- **Filtro por Marca**: Implementação de filtro no backend para os resultados obtidos.
- **Interface Responsiva**: Exibição em cards modernos inspirada no design do ML.

## 📂 Estrutura do Projeto

```text
├── services/
│   ├── auth.py          # Lógica de tokens e OAuth 2.0
│   └── mercado_livre.py # Integração com endpoints de produtos
├── static/
│   └── styles.css       # Estilização (Vanilla CSS)
├── templates/
│   └── index.html       # Interface principal (Jinja2)
├── app.py               # Servidor Flask e rotas
├── requirements.txt     # Dependências do projeto
├── .env.example         # Template de variáveis de ambiente
└── README.md            # Documentação
```

## 🛠️ Configuração

### 1. Requisitos
- Python 3.10 ou superior
- Uma aplicação criada no https://developers.mercadolivre.com.br/pt_br/api-docs-pt-br

### 2. Instalação
Clone o repósitório (ou copie os arquivos) e instale as dependências:
```bash
pip install -r requirements.txt
```

### 3. Variáveis de Ambiente
Renomeie o arquivo `.env.example` para `.env` e preencha suas credenciais:
```text
ML_CLIENT_ID=seu_client_id
ML_CLIENT_SECRET=seu_client_secret
ML_REDIRECT_URI=http://localhost:5000/callback
FLASK_SECRET_KEY=uma_chave_segura
```

### 4. Execução
Execute o servidor Flask:
```bash
python app.py
```
Acesse `http://localhost:5000` no seu navegador.

## 📘 Notas de Desenvolvimento

- **Serviços**: A lógica de negócio está separada em `services/` para facilitar testes e manutenção.
- **OAuth**: O fluxo de autenticação redireciona o usuário para o Mercado Livre e captura o `code` na rota `/callback`.
- **Filtro**: O filtro por marca é case-insensitive e busca o atributo `BRAND` dentro da lista de atributos do produto.
- **Mock**: No primeiro acesso, sem preencher o `.env`, o sistema solicitará o login. Para testar sem API, as funções podem ser adaptadas para retornar dados mockados na classe `MercadoLivreService`.

