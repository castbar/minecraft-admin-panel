FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements de Django
COPY panel/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código Django
COPY panel/ .

# NOTA: El frontend se sirve desde Nginx (servicio separado)
# Django solo maneja APIs y admin, no necesita el frontend compilado

# Exponer puerto
EXPOSE 8000

# Copiar y hacer ejecutable entrypoint
COPY panel/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Comando para iniciar Django
ENTRYPOINT ["/entrypoint.sh"]
