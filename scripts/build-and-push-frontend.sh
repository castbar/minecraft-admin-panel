#!/bin/bash
# Script para construir y subir imagen del frontend Ionic al registry

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
REGISTRY="${DOCKER_REGISTRY:-registry.castbar.dev}"
NAMESPACE="castbar"
IMAGE_NAME="minecraft-admin-frontend"
VERSION="${1:-latest}"

FULL_IMAGE="${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}:${VERSION}"

# Ir al directorio raíz del proyecto
cd "$(dirname "$0")/.."

echo -e "${BLUE}📦 Construyendo imagen frontend: ${FULL_IMAGE}${NC}"

# Compilar frontend si existe
if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
    echo -e "${BLUE}🔨 Compilando frontend...${NC}"
    cd frontend
    
    # Verificar si node_modules existe, si no, instalar
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}📦 Instalando dependencias del frontend...${NC}"
        npm install --legacy-peer-deps
    fi
    
    # Compilar con baseHref correcto
    echo -e "${BLUE}🔨 Compilando para producción...${NC}"
    npm run build -- --configuration production --base-href=/
    
    # Verificar que se compiló correctamente
    if [ ! -f "dist/index.html" ]; then
        echo -e "${YELLOW}⚠️  Advertencia: dist/index.html no encontrado después de compilar${NC}"
        echo -e "${YELLOW}   Verificando estructura de dist...${NC}"
        ls -la dist/ || echo "Directorio dist no existe"
    else
        echo -e "${GREEN}✅ Frontend compilado correctamente en dist/${NC}"
    fi
    
    cd ..
else
    echo -e "${YELLOW}⚠️  Frontend no encontrado o sin package.json${NC}"
    echo -e "${YELLOW}   Creando estructura mínima...${NC}"
    mkdir -p frontend/dist
    echo "<!DOCTYPE html><html><head><title>Frontend no compilado</title></head><body><h1>Frontend no compilado</h1><p>Compila el frontend Ionic antes de construir la imagen.</p></body></html>" > frontend/dist/index.html
fi

# Construir imagen desde el directorio frontend
echo -e "${BLUE}🐳 Construyendo imagen Docker del frontend...${NC}"
echo -e "${BLUE}   Contexto: frontend/${NC}"
echo -e "${BLUE}   Dockerfile: frontend/Dockerfile${NC}"

# Verificar que Dockerfile existe
if [ ! -f "frontend/Dockerfile" ]; then
    echo -e "${YELLOW}⚠️  Dockerfile no encontrado, creando uno básico...${NC}"
    cat > frontend/Dockerfile << 'EOF'
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY dist/ /usr/share/nginx/html/
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF
fi

# Verificar que nginx.conf existe
if [ ! -f "frontend/nginx.conf" ]; then
    echo -e "${YELLOW}⚠️  nginx.conf no encontrado, usando configuración por defecto${NC}"
fi

# Construir y publicar
docker buildx build --platform linux/amd64 -t "${FULL_IMAGE}" -f frontend/Dockerfile frontend/ --push

echo -e "${GREEN}✅ Imagen construida y subida${NC}"

# Si se especificó una versión, también crear tag 'latest'
if [ "$VERSION" != "latest" ]; then
    LATEST_TAG="${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}:latest"
    echo -e "${YELLOW}🏷️  Creando tag 'latest'...${NC}"
    docker tag "${FULL_IMAGE}" "${LATEST_TAG}"
    docker push "${LATEST_TAG}"
    echo -e "${GREEN}✅ Tag 'latest' creado${NC}"
fi

echo -e "${GREEN}🎉 Proceso completado${NC}"

