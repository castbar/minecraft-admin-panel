#!/bin/bash
# Script de diagnóstico completo para Tailscale - Requisitos del Kernel
# Ejecutar en el servidor APS: bash diagnostico-tailscale-kernel.sh

echo "============================================"
echo "DIAGNÓSTICO TAILSCALE - REQUISITOS KERNEL"
echo "============================================"
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para mostrar resultado
check_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

warn_result() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo "1. INFORMACIÓN DEL SISTEMA"
echo "---------------------------"
echo "Kernel version: $(uname -r)"
echo "Sistema operativo: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2 2>/dev/null || echo 'Desconocido')"
echo ""

echo "2. DISPOSITIVO TUN/TAP"
echo "----------------------"
if [ -c /dev/net/tun ]; then
    check_result 0 "Dispositivo /dev/net/tun existe"
    ls -l /dev/net/tun
else
    check_result 1 "Dispositivo /dev/net/tun NO EXISTE"
    echo "   Acción requerida: Crear dispositivo TUN"
    echo "   Comando: sudo mkdir -p /dev/net && sudo mknod /dev/net/tun c 10 200 && sudo chmod 666 /dev/net/tun"
fi
echo ""

echo "3. MÓDULO TUN DEL KERNEL"
echo "------------------------"
if lsmod | grep -q "^tun "; then
    check_result 0 "Módulo TUN está cargado"
    lsmod | grep "^tun "
else
    warn_result "Módulo TUN NO está cargado"
    echo "   Intentando cargar módulo TUN..."
    if sudo modprobe tun 2>/dev/null; then
        check_result 0 "Módulo TUN disponible y cargado correctamente"
    else
        check_result 1 "Módulo TUN NO disponible en el kernel"
        echo "   ERROR CRÍTICO: El kernel no tiene soporte TUN compilado"
        echo "   Acción requerida: Solicitar al proveedor habilitar CONFIG_TUN en el kernel"
        if [ -f /proc/config.gz ]; then
            echo "   Configuración actual:"
            zgrep CONFIG_TUN /proc/config.gz 2>/dev/null || echo "   CONFIG_TUN no encontrado en configuración"
        elif [ -f /boot/config-$(uname -r) ]; then
            echo "   Configuración actual:"
            grep CONFIG_TUN /boot/config-$(uname -r) 2>/dev/null || echo "   CONFIG_TUN no encontrado en configuración"
        fi
    fi
fi
echo ""

echo "4. SOPORTE WIREGUARD"
echo "--------------------"
KERNEL_VERSION=$(uname -r | cut -d'.' -f1,2)
KERNEL_MAJOR=$(echo $KERNEL_VERSION | cut -d'.' -f1)
KERNEL_MINOR=$(echo $KERNEL_VERSION | cut -d'.' -f2)

if [ "$KERNEL_MAJOR" -gt 5 ] || ([ "$KERNEL_MAJOR" -eq 5 ] && [ "$KERNEL_MINOR" -ge 6 ]); then
    check_result 0 "Kernel >= 5.6 (WireGuard incluido nativamente)"
else
    warn_result "Kernel < 5.6 (requiere módulo wireguard)"
fi

if lsmod | grep -q "^wireguard "; then
    check_result 0 "Módulo WireGuard está cargado"
    lsmod | grep "^wireguard "
else
    warn_result "Módulo WireGuard NO está cargado"
    echo "   Intentando cargar módulo WireGuard..."
    if sudo modprobe wireguard 2>/dev/null; then
        check_result 0 "Módulo WireGuard disponible y cargado correctamente"
    else
        check_result 1 "Módulo WireGuard NO disponible"
        echo "   ERROR CRÍTICO: El kernel no tiene soporte WireGuard"
        echo "   Acción requerida:"
        echo "   - Opción A: Actualizar kernel a >= 5.6"
        echo "   - Opción B: Solicitar al proveedor compilar kernel con CONFIG_WIREGUARD=y o CONFIG_WIREGUARD=m"
        echo "   - Opción C: Instalar módulo wireguard-linux-compat (para kernels < 5.6)"
        if [ -f /proc/config.gz ]; then
            echo "   Configuración actual:"
            zgrep CONFIG_WIREGUARD /proc/config.gz 2>/dev/null || echo "   CONFIG_WIREGUARD no encontrado en configuración"
        elif [ -f /boot/config-$(uname -r) ]; then
            echo "   Configuración actual:"
            grep CONFIG_WIREGUARD /boot/config-$(uname -r) 2>/dev/null || echo "   CONFIG_WIREGUARD no encontrado en configuración"
        fi
    fi
fi
echo ""

echo "5. PERMISOS Y CAPABILITIES"
echo "--------------------------"
if command -v tailscaled >/dev/null 2>&1; then
    TAILSCALED_PATH=$(which tailscaled)
    if [ -n "$TAILSCALED_PATH" ]; then
        CAPS=$(getcap "$TAILSCALED_PATH" 2>/dev/null)
        if echo "$CAPS" | grep -q "cap_net_admin"; then
            check_result 0 "tailscaled tiene CAP_NET_ADMIN"
            echo "   $CAPS"
        else
            warn_result "tailscaled NO tiene CAP_NET_ADMIN configurado"
            echo "   Verificando si se ejecuta como root..."
            if ps aux | grep -v grep | grep -q "^root.*tailscaled"; then
                check_result 0 "tailscaled se ejecuta como root (permisos OK)"
            else
                warn_result "tailscaled no se ejecuta como root"
            fi
        fi
    fi
else
    warn_result "tailscaled no encontrado en PATH"
fi
echo ""

echo "6. ESTADO DE TAILSCALE"
echo "--------------------"
if command -v tailscale >/dev/null 2>&1; then
    echo "Verificando estado de Tailscale..."
    sudo tailscale status 2>&1 | head -10
    echo ""
    echo "Ejecutando netcheck (puede tardar unos segundos)..."
    sudo tailscale netcheck 2>&1
else
    warn_result "Comando tailscale no encontrado"
fi
echo ""

echo "7. LOGS DE TAILSCALE (últimas 20 líneas)"
echo "----------------------------------------"
if systemctl is-active --quiet tailscaled 2>/dev/null; then
    echo "Últimas líneas del log (buscando errores relacionados con TUN/WireGuard):"
    sudo journalctl -u tailscaled -n 20 --no-pager 2>/dev/null | grep -iE "tun|wireguard|permission|error|failed" || echo "No se encontraron errores relacionados"
else
    warn_result "Servicio tailscaled no está activo"
fi
echo ""

echo "============================================"
echo "RESUMEN"
echo "============================================"
echo ""
echo "Para que Tailscale funcione correctamente, se requieren:"
echo "1. ✅ Dispositivo /dev/net/tun existente"
echo "2. ✅ Módulo TUN del kernel disponible"
echo "3. ✅ Soporte WireGuard (kernel >= 5.6 o módulo wireguard)"
echo "4. ✅ Permisos adecuados (root o CAP_NET_ADMIN)"
echo ""
echo "Si alguno de estos puntos falla, contactar al proveedor con:"
echo "- Este reporte completo"
echo "- Solicitud específica según los errores encontrados"
echo ""
