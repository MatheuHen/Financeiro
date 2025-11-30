FINANCEIRO — Sistema de Extração e Processamento de NF-e

Este projeto é um sistema completo para extrair dados de Notas Fiscais (PDF ou imagem), processar automaticamente as informações e consultar tudo via RAG (inteligência artificial contextualizada no banco).
É uma solução pensada para automatizar rotinas de contas a pagar/receber, organizando fornecedores, faturados, classificações e movimentações financeiras.

🚀 Funcionalidades Principais
🔹 Agente 01 — Extração da NF-e

Responsável por interpretar a nota fiscal (PDF/JPG/PNG) usando IA (Gemini):

Identifica fornecedor, faturado, produtos, parcelas e totais

Normaliza valores

Entende respostas estruturadas em JSON

Classifica automaticamente DESPESA/RECEITA

Determina se a conta é PAGAR ou RECEBER

🔹 Agente 02 — Processamento

A partir dos dados extraídos:

Cria fornecedor/cliente se não existirem

Consulta ou cria classificações (Receita/Despesa)

Registra o movimento financeiro

Registra parcelas

Armazena os produtos em itens_json

Suporta múltiplas classificações na mesma conta

🔹 Agente 03 — RAG (Consulta Inteligente)

Permite fazer perguntas sobre o banco de dados usando IA:

RAG Simples (palavras-chave)

RAG por Embeddings (similaridade semântica)

Respostas elaboradas com contexto real do sistema

🛠️ Tecnologias Utilizadas

Backend: Django 5 + Django REST Framework

Frontend: HTML, Bootstrap e JavaScript puro

IA: Google Gemini

Banco: SQLite (desenvolvimento) / PostgreSQL (produção)

Contêiner: Docker + Docker Compose

Serviço estático e deploy: suporte a WhiteNoise e Nginx

📦 Como rodar em Desenvolvimento (Docker)
git clone https://github.com/MatheuHen/Financeiro
cd Financeiro
docker compose -f "docker-compose.dev.yml" up -d --remove-orphans


Acesse:

Sistema → http://localhost:8000

Admin → http://localhost:8000/admin

Health → http://localhost:8000/health/

🌐 Acesso em Produção (Deploy Render)

O sistema já está publicado e pode ser acessado diretamente pelo link:

👉 https://financeiro-ajcb.onrender.com/menu/

Rotas principais no ambiente de produção:

Menu principal:
https://financeiro-ajcb.onrender.com/menu/

Extração de NF-e:
https://financeiro-ajcb.onrender.com/extracao/

Cadastros (Pessoas, Classificações, Movimentos):
https://financeiro-ajcb.onrender.com/gerenciar/

Health Check (status do sistema):
https://financeiro-ajcb.onrender.com/health/

🗂️ Estrutura do Projeto (resumo)
api/
 ├── agente01.py            # Extração da NF-e (IA)
 ├── agente02.py            # Processamento e persistência
 ├── agente03.py            # RAG (Simples + Embeddings)
 ├── views.py               # Rotas principais e health check
 ├── gerenciamento_views.py # UI de cadastros
 ├── models.py              # Pessoas, Classificação, Movimento, Parcelas
 ├── templates/             # HTML do sistema
 └── static/                # CSS/JS
nfe_project/                # settings, urls e wsgi
docker-compose.dev.yml
docker-compose.yml
Dockerfile
entrypoint.sh
requirements.txt
scripts/seed.sqlite.sql     # Base com +200 registros

🧩 Regras de Interface

Tabelas começam vazias

Dados só aparecem ao clicar Buscar ou Todos

“Todos” → traz apenas registros ATIVOS

Ordenação por coluna

Suporte a busca por múltiplos campos

Editar / Excluir (exclusão lógica → INATIVO)

CREATE/UPDATE não mostram campo de status

🧠 Detalhes da Extração

O sistema obtém automaticamente:

Fornecedor (razão social, CNPJ)

Faturado (nome, CPF)

Número, série, data e total da nota

Itens da nota (descrição, quantidades e valores)

Parcelas (datas e valores)

Tipo da movimentação (Receita/Despesa, Pagar/Receber)

🔍 RAG — Perguntas Inteligentes

Você pode perguntar coisas como:

"Quanto já gastei com manutenção este mês?"

"Quais fornecedores foram usados em outubro?"

"Liste as notas classificadas como despesa de operação"

O RAG usa embeddings e contexto real do banco.

🛠️ Solução de Problemas Comuns

Container não inicia

docker compose -f "docker-compose.dev.yml" down
docker compose -f "docker-compose.dev.yml" up -d --remove-orphans


Erro: “no such table: api_pessoas”
→ Configure DJANGO_DB_RUN=1 e reinicie.

Gemini não responde
→ Falta GEMINI_API_KEY.

📡 Monitoramento

Health: /health/

Logs locais:

docker compose -f "docker-compose.dev.yml" logs -f


Logs do servidor (Render): painel → Logs
