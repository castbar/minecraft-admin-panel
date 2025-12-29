# Dockerfile para frontend Ionic con Nginx
FROM nginx:alpine

# Instalar wget para health check
RUN apk add --no-cache wget

# Copiar configuración de Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar archivos del frontend compilado
# NOTA: El contexto de build es frontend/, así que dist/ está en el contexto
COPY dist/ /usr/share/nginx/html/

# Verificar que index.html existe, si no, crear uno temporal
RUN if [ ! -f /usr/share/nginx/html/index.html ]; then \
      echo '<!DOCTYPE html><html><head><title>Minecraft Admin Panel</title><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head><body style="font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f5f5f5;"><div style="text-align: center; padding: 2rem; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);"><h1 style="color: #667eea;">Frontend no compilado</h1><p>Compila el frontend Ionic antes de construir la imagen.</p></div></body></html>' > /usr/share/nginx/html/index.html; \
    fi

# Exponer puerto 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

# Iniciar Nginx
CMD ["nginx", "-g", "daemon off;"]

