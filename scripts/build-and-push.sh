#!/bin/bash
# Script para construir y subir imagen del panel Django al registry
# NOTA: Este script solo construye el backend Django (APIs y admin)
# El frontend se construye con build-and-push-frontend.sh

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
REGISTRY="${DOCKER_REGISTRY:-registry.castbar.dev}"
NAMESPACE="${DOCKER_NAMESPACE:-castbar}"
IMAGE_NAME="minecraft-admin-panel"
VERSION="${1:-latest}"

FULL_IMAGE="${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}:${VERSION}"

# Ir al directorio raíz del proyecto
cd "$(dirname "$0")/.."

echo -e "${BLUE}📦 Construyendo imagen del panel Django: ${FULL_IMAGE}${NC}"

# Verificar que el Dockerfile existe
if [ ! -f "panel/Dockerfile" ]; then
    echo -e "${YELLOW}❌ Error: panel/Dockerfile no encontrado${NC}"
    exit 1
fi

# Verificar que requirements.txt existe
if [ ! -f "panel/requirements.txt" ]; then
    echo -e "${YELLOW}❌ Error: panel/requirements.txt no encontrado${NC}"
    exit 1
fi

# Construir imagen desde el directorio raíz (contexto completo)
# El Dockerfile copia panel/ desde el contexto
echo -e "${BLUE}🐳 Construyendo imagen Docker...${NC}"
echo -e "${BLUE}   Contexto: . (directorio raíz)${NC}"
echo -e "${BLUE}   Dockerfile: panel/Dockerfile${NC}"

docker buildx build --platform linux/amd64 -t "${FULL_IMAGE}" -f panel/Dockerfile . --push

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
