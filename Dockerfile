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

# Copia entrypoint para execução de tarefas em runtime
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expõe a porta 8000
EXPOSE 8000

# Comando/entrypoint para iniciar a aplicação e executar tarefas de runtime
ENTRYPOINT ["/app/entrypoint.sh"]