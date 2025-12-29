#!/bin/bash
# Script para construir y subir imagen del panel Django al registry

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
REGISTRY="${DOCKER_REGISTRY:-registry.example.com}"
NAMESPACE="castbar"
IMAGE_NAME="minecraft-admin-panel"
VERSION="${1:-latest}"  # Usar versión pasada como argumento o 'latest' por defecto

FULL_IMAGE="${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}:${VERSION}"

echo -e "${BLUE}📦 Construyendo imagen: ${FULL_IMAGE}${NC}"

# Construir imagen
cd "$(dirname "$0")/../panel"
docker build -t "${FULL_IMAGE}" -f Dockerfile .

echo -e "${GREEN}✅ Imagen construida${NC}"

# Subir al registry
echo -e "${BLUE}📤 Subiendo al registry...${NC}"
docker push "${FULL_IMAGE}"

echo -e "${GREEN}✅ Imagen subida al registry${NC}"

# Si se especificó una versión, también crear tag 'latest'
if [ "$VERSION" != "latest" ]; then
    LATEST_TAG="${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}:latest"
    echo -e "${YELLOW}🏷️  Creando tag 'latest'...${NC}"
    docker tag "${FULL_IMAGE}" "${LATEST_TAG}"
    docker push "${LATEST_TAG}"
    echo -e "${GREEN}✅ Tag 'latest' creado${NC}"
fi

echo -e "${GREEN}🎉 Proceso completado${NC}"
echo -e "${BLUE}📋 Para marcar como LTS:${NC}"
echo -e "   docker tag ${FULL_IMAGE} ${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}:lts"
echo -e "   docker push ${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}:lts"

