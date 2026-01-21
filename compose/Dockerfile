
FROM python:3.13-slim


WORKDIR /compose

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Dependencias del sistema 
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev netcat-traditional \
  && rm -rf /var/lib/apt/lists/*

# Dependencias Python
COPY requirements.txt /compose/requirements.txt
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r /compose/requirements.txt

# Copiar el proyecto 
COPY . /compose

# Permisos + usuario no-root
RUN chmod +x /compose/entrypoint.sh \
 && useradd -m appuser \
 && mkdir -p /compose/staticfiles /compose/media \
 && chown -R appuser:appuser /compose


EXPOSE 8000
CMD ["/compose/entrypoint.sh"]
