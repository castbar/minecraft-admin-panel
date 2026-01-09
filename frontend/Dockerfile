# Etapa 1: Compilar el frontend Ionic
FROM node:20-alpine AS builder

WORKDIR /app

# Copiar archivos de dependencias
COPY package*.json ./

# Instalar dependencias
RUN npm ci

# Copiar código fuente
COPY . .

# Compilar el proyecto para producción
RUN npm run build -- --configuration=production

# Etapa 2: Servir con Nginx
FROM nginx:alpine

# Instalar wget para health check
RUN apk add --no-cache wget

# Copiar configuración de Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar archivos compilados desde la etapa de build
# Ionic/Angular compila a www/ o dist/
COPY --from=builder /app/www /usr/share/nginx/html

# Verificar que index.html existe
RUN if [ ! -f /usr/share/nginx/html/index.html ]; then \
      echo "ERROR: index.html no encontrado después del build" >&2; \
      exit 1; \
    fi

# Exponer puerto 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

# Iniciar Nginx
CMD ["nginx", "-g", "daemon off;"]
