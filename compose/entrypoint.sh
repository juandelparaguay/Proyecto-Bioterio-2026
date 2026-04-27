#!/usr/bin/env sh
set -o errexit
set -o pipefail

# Esperar a que la DB esté lista
if [ -n "${DB_HOST}" ]; then
  echo "Esperando a la base de datos ${DB_HOST}:${DB_PORT}..."
  until nc -z "${DB_HOST:-db}" "${DB_PORT:-5432}"; do
    sleep 1
  done
fi

# Migraciones y estáticos
echo "Preparando directorios de estáticos y media..."
mkdir -p /compose/staticfiles /compose/media
chown -R appuser:appuser /compose/staticfiles /compose/media
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Lanzar Gunicorn
exec gunicorn bioterio.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --timeout 60
