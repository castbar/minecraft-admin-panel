#!/bin/bash
# Script para construir imágenes localmente y transferirlas por SSH al servidor
# Uso: ./deploy-local-to-server.sh

set -e

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuración
SERVER_USER="carlitos"
SERVER_HOST="100.77.240.103"
SERVER_PATH="/home/carlitos/repos/minecraft-admin-panel"
IMAGE_TAG="latest"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${GREEN}🚀 Iniciando despliegue local a servidor${NC}"
echo "=========================================="

# Verificar que Docker está corriendo
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker no está corriendo${NC}"
    exit 1
fi

# 1. Construir imagen del panel (backend)
echo -e "\n${YELLOW}📦 Construyendo imagen del panel (backend)...${NC}"
cd "$PROJECT_DIR/panel"
docker build -t minecraft-admin-panel:${IMAGE_TAG} . || {
    echo -e "${RED}❌ Error construyendo imagen del panel${NC}"
    exit 1
}
echo -e "${GREEN}✅ Imagen del panel construida${NC}"

# 2. Construir imagen del frontend
echo -e "\n${YELLOW}📦 Construyendo imagen del frontend...${NC}"
cd "$PROJECT_DIR/frontend"
docker build -t minecraft-admin-frontend:${IMAGE_TAG} . || {
    echo -e "${RED}❌ Error construyendo imagen del frontend${NC}"
    exit 1
}
echo -e "${GREEN}✅ Imagen del frontend construida${NC}"

# 3. Guardar imágenes como tar
echo -e "\n${YELLOW}💾 Guardando imágenes como archivos tar...${NC}"
cd "$PROJECT_DIR"
docker save minecraft-admin-panel:${IMAGE_TAG} -o .temp/minecraft-admin-panel-${IMAGE_TAG}.tar || {
    echo -e "${RED}❌ Error guardando imagen del panel${NC}"
    exit 1
}
docker save minecraft-admin-frontend:${IMAGE_TAG} -o .temp/minecraft-admin-frontend-${IMAGE_TAG}.tar || {
    echo -e "${RED}❌ Error guardando imagen del frontend${NC}"
    exit 1
}
echo -e "${GREEN}✅ Imágenes guardadas${NC}"

# 4. Transferir imágenes al servidor
echo -e "\n${YELLOW}📤 Transferiendo imágenes al servidor...${NC}"
echo "Esto puede tardar varios minutos dependiendo del tamaño de las imágenes..."

scp .temp/minecraft-admin-panel-${IMAGE_TAG}.tar ${SERVER_USER}@${SERVER_HOST}:/tmp/ || {
    echo -e "${RED}❌ Error transfiriendo imagen del panel${NC}"
    exit 1
}
echo -e "${GREEN}✅ Imagen del panel transferida${NC}"

scp .temp/minecraft-admin-frontend-${IMAGE_TAG}.tar ${SERVER_USER}@${SERVER_HOST}:/tmp/ || {
    echo -e "${RED}❌ Error transfiriendo imagen del frontend${NC}"
    exit 1
}
echo -e "${GREEN}✅ Imagen del frontend transferida${NC}"

# 5. Cargar imágenes en el servidor
echo -e "\n${YELLOW}📥 Cargando imágenes en el servidor...${NC}"
ssh ${SERVER_USER}@${SERVER_HOST} << EOF
    set -e
    echo "Cargando imagen del panel..."
    docker load -i /tmp/minecraft-admin-panel-${IMAGE_TAG}.tar || {
        echo "❌ Error cargando imagen del panel"
        exit 1
    }
    echo "✅ Imagen del panel cargada"
    
    echo "Cargando imagen del frontend..."
    docker load -i /tmp/minecraft-admin-frontend-${IMAGE_TAG}.tar || {
        echo "❌ Error cargando imagen del frontend"
        exit 1
    }
    echo "✅ Imagen del frontend cargada"
    
    # Limpiar archivos temporales
    rm -f /tmp/minecraft-admin-panel-${IMAGE_TAG}.tar
    rm -f /tmp/minecraft-admin-frontend-${IMAGE_TAG}.tar
    echo "✅ Archivos temporales eliminados"
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Imágenes cargadas en el servidor${NC}"
else
    echo -e "${RED}❌ Error cargando imágenes en el servidor${NC}"
    exit 1
fi

# 6. Limpiar archivos locales
echo -e "\n${YELLOW}🧹 Limpiando archivos temporales locales...${NC}"
rm -f .temp/minecraft-admin-panel-${IMAGE_TAG}.tar
rm -f .temp/minecraft-admin-frontend-${IMAGE_TAG}.tar
echo -e "${GREEN}✅ Archivos temporales eliminados${NC}"

# 7. Instrucciones para desplegar
echo -e "\n${GREEN}✅ Despliegue completado${NC}"
echo "=========================================="
echo -e "${YELLOW}📋 Próximos pasos:${NC}"
echo "1. Conectarse al servidor:"
echo "   ssh ${SERVER_USER}@${SERVER_HOST}"
echo ""
echo "2. Ir al directorio del proyecto:"
echo "   cd ${SERVER_PATH}"
echo ""
echo "3. Detener contenedores actuales:"
echo "   docker compose down"
echo ""
echo "4. Actualizar docker-compose.yml para usar las imágenes locales:"
echo "   # Cambiar 'build:' por 'image:' con los nombres:"
echo "   # minecraft-admin-panel:${IMAGE_TAG}"
echo "   # minecraft-admin-frontend:${IMAGE_TAG}"
echo ""
echo "5. Levantar contenedores:"
echo "   docker compose up -d"
echo ""
echo "6. Verificar logs:"
echo "   docker compose logs -f"
