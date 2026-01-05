#!/bin/bash
# Script para obtener información de Tailscale y configuración del panel

echo "=== Información del Sistema ==="
hostname
echo ""

echo "=== IPs del Servidor ==="
hostname -I
echo ""

echo "=== IP de Tailscale ==="
if command -v tailscale &> /dev/null; then
    tailscale ip -4
    echo ""
    echo "=== Estado de Tailscale ==="
    tailscale status | head -10
else
    echo "Tailscale no está instalado o no está en el PATH"
fi
echo ""

echo "=== Contenedores Docker del Panel ==="
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E 'minecraft-admin|NAMES'
echo ""

echo "=== Puerto del Frontend ==="
if [ -f ~/minecraft-admin-panel/docker-compose.yml ]; then
    grep "FRONTEND_PORT" ~/minecraft-admin-panel/docker-compose.yml || grep "8080" ~/minecraft-admin-panel/docker-compose.yml | head -1
elif [ -f ~/docker-compose.yml ]; then
    grep "FRONTEND_PORT" ~/docker-compose.yml || grep "8080" ~/docker-compose.yml | head -1
else
    echo "docker-compose.yml no encontrado en ~/ o ~/minecraft-admin-panel/"
fi
echo ""

echo "=== Información para el Usuario ==="
TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || echo "NO_DISPONIBLE")
FRONTEND_PORT=$(grep -E "FRONTEND_PORT|8080" ~/minecraft-admin-panel/docker-compose.yml ~/docker-compose.yml 2>/dev/null | grep -oE "8080|:\"[0-9]+\"" | head -1 | tr -d ':"' || echo "8080")

echo "URL para acceder al panel:"
if [ "$TAILSCALE_IP" != "NO_DISPONIBLE" ]; then
    echo "  http://${TAILSCALE_IP}:${FRONTEND_PORT}"
else
    echo "  (Necesita IP de Tailscale)"
fi







