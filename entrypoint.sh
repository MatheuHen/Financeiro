#!/usr/bin/env sh
set -e

echo "[entrypoint] Inicializando container..."

echo "[entrypoint] Coletando arquivos estáticos..."
python manage.py collectstatic --noinput || echo "[entrypoint] collectstatic falhou; seguindo mesmo assim"

if [ -n "$DJANGO_DB_RUN" ]; then
  echo "[entrypoint] Executando migrações do banco..."
  python manage.py migrate --noinput || echo "[entrypoint] migrate falhou; seguindo mesmo assim"

  echo "[entrypoint] Executando setup_inicial..."
  python manage.py setup_inicial || echo "[entrypoint] setup_inicial falhou; seguindo mesmo assim"
else
  echo "[entrypoint] Pulando migrações e setup_inicial (defina DJANGO_DB_RUN=1 para habilitar)"
fi

echo "[entrypoint] Iniciando servidor Django..."
exec python manage.py runserver 0.0.0.0:8000