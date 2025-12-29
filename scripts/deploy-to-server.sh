#!/bin/bash
# Script para desplegar imagen desde registry al servidor

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
TAG="${1:-lts}"  # Usar tag pasado como argumento o 'lts' por defecto
SERVER_USER="${2:-carlitos}"
SERVER_HOST="${3:-localhost}"

FULL_IMAGE="${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}:${TAG}"

echo -e "${BLUE}🚀 Desplegando ${FULL_IMAGE} a ${SERVER_USER}@${SERVER_HOST}${NC}"

# Conectar al servidor y desplegar
ssh "${SERVER_USER}@${SERVER_HOST}" << EOF
    set -e
    echo "📥 Descargando imagen del registry..."
    docker pull ${FULL_IMAGE}
    
    echo "🔄 Actualizando contenedor..."
    cd ~ && docker compose -f docker-compose.yml up -d minecraft-admin-panel
    
    echo "⏳ Esperando que Django inicie..."
    sleep 5
    
    echo "✅ Despliegue completado"
    echo "📋 Estado del contenedor:"
    docker ps | grep minecraft-admin-panel
EOF

echo -e "${GREEN}🎉 Despliegue completado${NC}"
echo -e "${YELLOW}⚠️  NOTA: El servidor Minecraft NO se reinició${NC}"

