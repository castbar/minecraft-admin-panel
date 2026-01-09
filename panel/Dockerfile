FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements de Django
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código Django
COPY . .

# NOTA: El frontend se sirve desde Nginx (servicio separado)
# Django solo maneja APIs y admin, no necesita el frontend compilado

# Exponer puerto
EXPOSE 8000

# Copiar entrypoint y asegurar formato Unix
COPY entrypoint.sh /entrypoint.sh
RUN apt-get update && apt-get install -y dos2unix && \
    dos2unix /entrypoint.sh && \
    chmod +x /entrypoint.sh && \
    rm -rf /var/lib/apt/lists/*

# Comando para iniciar Django
ENTRYPOINT ["/entrypoint.sh"]
