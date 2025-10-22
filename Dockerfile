# Use uma imagem base do Python
FROM python:3.11-slim

# Define o diretório de trabalho
WORKDIR /app

# Instala dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copia o arquivo de requisitos
COPY requirements.txt .

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código da aplicação
COPY . .

# Cria o diretório para arquivos estáticos
RUN mkdir -p /app/staticfiles

# Coleta arquivos estáticos
RUN python manage.py collectstatic --noinput

# Executa as migrações do banco de dados
RUN python manage.py migrate

# Cria dados iniciais
RUN python manage.py setup_inicial

# Expõe a porta 8000
EXPOSE 8000

# Comando para iniciar a aplicação
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]