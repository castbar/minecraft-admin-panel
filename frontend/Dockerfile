# Dockerfile para frontend Ionic con Nginx
FROM nginx:alpine

# Instalar wget para health check
RUN apk add --no-cache wget

# Copiar configuración de Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar archivos del frontend compilado
# NOTA: El contexto de build es frontend/, así que dist/ está en el contexto
COPY dist/ /usr/share/nginx/html/

# Verificar que index.html existe
RUN if [ ! -f /usr/share/nginx/html/index.html ]; then \
      echo "ERROR: index.html no encontrado en dist/" >&2; \
      exit 1; \
    fi

# Exponer puerto 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

# Iniciar Nginx
CMD ["nginx", "-g", "daemon off;"]

