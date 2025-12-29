#!/bin/bash
# Script para construir y subir ambas imágenes (frontend y backend)

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
VERSION="${1:-latest}"

# Ir al directorio raíz del proyecto
cd "$(dirname "$0")/.."

echo -e "${BLUE}🚀 Construyendo y publicando todas las imágenes${NC}"
echo -e "${BLUE}   Versión: ${VERSION}${NC}"
echo ""

# 1. Construir y publicar frontend
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📦 PASO 1: Frontend Ionic${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
./scripts/build-and-push-frontend.sh "${VERSION}"

echo ""

# 2. Construir y publicar backend
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📦 PASO 2: Backend Django${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
./scripts/build-and-push.sh "${VERSION}"

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ TODAS LAS IMÁGENES CONSTRUIDAS Y PUBLICADAS${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}📋 Resumen:${NC}"
echo -e "   Frontend: registry.castbar.dev/castbar/minecraft-admin-frontend:${VERSION}"
echo -e "   Backend:  registry.castbar.dev/castbar/minecraft-admin-panel:${VERSION}"
echo ""

