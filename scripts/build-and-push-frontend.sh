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
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}📦 Instalando dependencias del frontend...${NC}"
        npm install --legacy-peer-deps
    fi
    npm run build -- --configuration production
    cd ..
    echo -e "${GREEN}✅ Frontend compilado${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend no encontrado, creando directorio vacío${NC}"
    mkdir -p frontend/dist
    touch frontend/dist/.gitkeep
fi

# Construir imagen desde el directorio frontend
echo -e "${BLUE}🐳 Construyendo imagen Docker...${NC}"
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

