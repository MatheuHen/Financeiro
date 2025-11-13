# FINANCEIRO - Sistema de Extração e Processamento de NFe

Sistema completo para extração de dados de Notas Fiscais Eletrônicas (NFe) e processamento automático no banco de dados financeiro.

## 🚀 Funcionalidades

### Agente 01 - Extração de Dados
- Extração automática de dados de NFe (XML/PDF)
- Identificação de fornecedor, cliente e produtos
- Normalização de valores monetários
- Cálculo automático de totais e parcelas

### Agente 02 - Processamento no Banco
- Criação automática de fornecedores e clientes
- Registro de movimentos financeiros
- Geração de parcelas de pagamento
- Classificação automática de despesas

## 🛠️ Tecnologias

- **Backend**: Django + Django REST Framework
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **IA**: Google Gemini para extração de dados
- **Banco de Dados**: SQLite (desenvolvimento) / PostgreSQL (produção)
- **Containerização**: Docker + Docker Compose

## 📋 Pré-requisitos

- Docker
- Docker Compose
- Git

## 🚀 Como Executar

### 1. Clone o repositório
```bash
git clone <url-do-repositorio>
cd FINANCEIRO
```

### 2. Execute com Docker Compose
```bash
docker-compose up
```

### 3. Acesse o sistema
Após a inicialização, acesse:
- **Sistema Web**: [http://localhost:8000](http://localhost:8000)
- **Admin Django**: [http://localhost:8000/admin](http://localhost:8000/admin)

## 📁 Estrutura do Projeto

```
FINANCEIRO/
├── api/                    # Backend Django
│   ├── agente01.py        # Extração de dados NFe
│   ├── agente02.py        # Processamento banco de dados
│   ├── models.py          # Modelos do banco
│   ├── views.py           # APIs REST
│   └── static/            # Arquivos estáticos
├── docker-compose.yml     # Configuração Docker
├── Dockerfile            # Imagem Docker
└── requirements.txt      # Dependências Python
```

## 🔧 Configuração

### Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto:

```env
DJANGO_SECRET_KEY=sua-chave-secreta
GEMINI_API_KEY=sua-chave-gemini
DEBUG=True
```

### Banco de Dados
O sistema criará automaticamente as tabelas necessárias na primeira execução.

## 📊 Como Usar

1. **Acesse o sistema** em http://localhost:8000
2. **Selecione a aba** desejada:
   - **Agente 01**: Para extrair dados de NFe
   - **Agente 02**: Para consultar dados salvos
3. **Faça upload** de uma NFe (XML ou PDF)
4. **Visualize os dados** extraídos
5. **Confirme o salvamento** no banco de dados

## 🔍 Funcionalidades Detalhadas

### Interface com Abas
- **Agente 01**: Extração e visualização de dados
- **Agente 02**: Consulta de dados existentes no banco
- **Confirmação**: Sistema pergunta antes de salvar novos dados

### Dados Extraídos
- **Fornecedor**: Nome, CNPJ, endereço
- **Cliente**: Nome, CPF/CNPJ
- **Produtos**: Descrição, quantidade, valor unitário, valor total
- **Parcelas**: Número, valor, data de vencimento

### Processamento Automático
- Criação de fornecedores e clientes (se não existirem)
- Registro de movimentos financeiros
- Geração automática de parcelas
- Classificação de despesas

## 🐛 Solução de Problemas

### Container não inicia
```bash
docker-compose down
docker-compose up --build
```

### Erro de permissão
```bash
sudo docker-compose up
```

### Logs do sistema
```bash
docker-compose logs -f
```

## 📝 Logs e Monitoramento

O sistema gera logs detalhados de todas as operações:
- Extração de dados (Agente 01)
- Processamento no banco (Agente 02)
- Erros e exceções

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request
