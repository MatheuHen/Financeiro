# Sistema Financeiro - Docker

Este documento explica como executar o Sistema Financeiro usando Docker.

## Pré-requisitos

- Docker instalado
- Docker Compose instalado
- Arquivo `.env` configurado com `GEMINI_API_KEY`

## Configuração do Ambiente

1. Certifique-se de que o arquivo `.env` existe na raiz do projeto com:
```
GEMINI_API_KEY=sua_chave_aqui
SECRET_KEY=django-insecure-!0)_0s7*0u4u9z8yr(mm$^qt$mrvran(ej9z-te!(m0-yi=d7
DEBUG=1
```

## Execução

### Desenvolvimento (SQLite)

Para desenvolvimento local usando SQLite:

```bash
docker-compose -f docker-compose.dev.yml up --build
```

A aplicação estará disponível em: http://localhost:8000

### Produção (PostgreSQL + Nginx)

Para ambiente de produção com PostgreSQL e Nginx:

```bash
docker-compose up --build
```

A aplicação estará disponível em:
- Frontend: http://localhost (porta 80)
- API Django: http://localhost:8000 (acesso direto)
- PostgreSQL: localhost:5432

## Comandos Úteis

### Parar os containers
```bash
docker-compose down
```

### Parar e remover volumes
```bash
docker-compose down -v
```

### Ver logs
```bash
docker-compose logs -f web
```

### Executar comandos Django no container
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py setup_inicial
```

### Rebuild apenas a aplicação
```bash
docker-compose up --build web
```

## Estrutura dos Containers

- **web**: Aplicação Django
- **db**: PostgreSQL (apenas em produção)
- **nginx**: Proxy reverso (apenas em produção)

## Volumes

- **postgres_data**: Dados do PostgreSQL
- **static_volume**: Arquivos estáticos do Django
- **media_volume**: Arquivos de mídia/upload

## Portas

- 80: Nginx (produção)
- 8000: Django (desenvolvimento e acesso direto)
- 5432: PostgreSQL (produção)

## Troubleshooting

### Erro de permissão
Se houver erro de permissão, execute:
```bash
sudo chown -R $USER:$USER .
```

### Limpar tudo e recomeçar
```bash
docker-compose down -v
docker system prune -a
docker-compose up --build
```

### Verificar logs de erro
```bash
docker-compose logs web
docker-compose logs db
docker-compose logs nginx
```