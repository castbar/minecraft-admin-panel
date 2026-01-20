# Diagnóstico Tailscale - Servidor APS

## Problema
Tailscale no funciona en el servidor APS (200.35.159.44), impidiendo la conexión VPN mesh con el servidor local (100.77.240.103).

## Requisitos Técnicos de Tailscale

### ⚠️ CRÍTICO: Requisitos del Kernel

Tailscale **REQUIERE** soporte del kernel para funcionar. Estos son los requisitos más importantes y frecuentemente olvidados:

#### 1. Dispositivo TUN/TAP (`/dev/net/tun`)
**CRÍTICO:** Tailscale necesita crear interfaces de red virtuales mediante el dispositivo TUN.

**Verificar:**
```bash
# Verificar que existe el dispositivo
ls -l /dev/net/tun

# Debe mostrar algo como:
# crw-rw-rw- 1 root root 10, 200 [fecha] /dev/net/tun
```

**Si no existe, crear:**
```bash
sudo mkdir -p /dev/net
sudo mknod /dev/net/tun c 10 200
sudo chmod 666 /dev/net/tun
```

#### 2. Módulo del Kernel `tun`
**CRÍTICO:** El kernel debe tener el módulo `tun` disponible y cargado.

**Verificar:**
```bash
# Verificar si el módulo está cargado
lsmod | grep tun

# Intentar cargar el módulo
sudo modprobe tun

# Verificar si está disponible (aunque no esté cargado)
find /lib/modules/$(uname -r) -name "tun.ko"
```

**Si falla `modprobe tun`:**
- El kernel no tiene soporte TUN compilado
- Necesita kernel con `CONFIG_TUN=y` o `CONFIG_TUN=m`
- **Solicitar al proveedor:** Habilitar módulo TUN en el kernel

#### 3. Soporte de WireGuard en el Kernel
**CRÍTICO:** Tailscale usa WireGuard, que requiere soporte del kernel.

**Requisitos:**
- **Kernel >= 5.6:** WireGuard está incluido en el kernel
- **Kernel < 5.6:** Necesita módulo `wireguard` o `wireguard-linux-compat`

**Verificar versión del kernel:**
```bash
uname -r
```

**Verificar soporte de WireGuard:**
```bash
# Verificar si el módulo está cargado
lsmod | grep wireguard

# Intentar cargar el módulo
sudo modprobe wireguard

# Verificar configuración del kernel (si está disponible)
zgrep CONFIG_WIREGUARD /proc/config.gz 2>/dev/null || \
grep CONFIG_WIREGUARD /boot/config-$(uname -r) 2>/dev/null
```

**Si `modprobe wireguard` falla:**
- Kernel < 5.6 sin módulo wireguard instalado
- Kernel compilado sin soporte WireGuard
- **Solicitar al proveedor:** 
  - Actualizar a kernel >= 5.6, O
  - Instalar módulo `wireguard-linux-compat`, O
  - Compilar kernel con `CONFIG_WIREGUARD=y` o `CONFIG_WIREGUARD=m`

#### 4. Permisos del Sistema
**CRÍTICO:** `tailscaled` necesita permisos de administrador de red.

**Verificar:**
```bash
# Verificar que tailscaled tiene CAP_NET_ADMIN
getcap $(which tailscaled) 2>/dev/null || echo "No capabilities set"

# Verificar permisos del proceso
ps aux | grep tailscaled
```

**Requisito:** `tailscaled` debe ejecutarse como root o con `CAP_NET_ADMIN`.

#### 5. Verificación Completa del Kernel
**Comando de diagnóstico completo:**
```bash
echo "=== DIAGNÓSTICO KERNEL TAILSCALE ==="
echo "Kernel version: $(uname -r)"
echo ""
echo "1. Dispositivo TUN:"
ls -l /dev/net/tun 2>&1 || echo "❌ /dev/net/tun NO EXISTE"
echo ""
echo "2. Módulo TUN:"
lsmod | grep -q tun && echo "✅ Módulo TUN cargado" || echo "❌ Módulo TUN NO cargado"
modprobe tun 2>&1 && echo "✅ Módulo TUN disponible" || echo "❌ Módulo TUN NO disponible"
echo ""
echo "3. WireGuard:"
lsmod | grep -q wireguard && echo "✅ Módulo WireGuard cargado" || echo "⚠️  Módulo WireGuard NO cargado"
modprobe wireguard 2>&1 && echo "✅ Módulo WireGuard disponible" || echo "❌ Módulo WireGuard NO disponible"
echo ""
echo "4. Configuración del kernel:"
if [ -f /proc/config.gz ]; then
    zgrep -E "CONFIG_TUN|CONFIG_WIREGUARD" /proc/config.gz 2>/dev/null
elif [ -f /boot/config-$(uname -r) ]; then
    grep -E "CONFIG_TUN|CONFIG_WIREGUARD" /boot/config-$(uname -r) 2>/dev/null
else
    echo "⚠️  No se puede acceder a la configuración del kernel"
fi
```

### Requisitos de Red (Puertos y Protocolos)

Tailscale requiere los siguientes puertos y protocolos para funcionar correctamente:

### Puertos Salientes (Outbound)
| Puerto | Protocolo | Propósito | Crítico |
|--------|-----------|-----------|---------|
| **443** | TCP | Control plane y servidores DERP (relays) | ✅ SÍ |
| **41641** | UDP | Túneles WireGuard peer-to-peer | ✅ SÍ |
| **3478** | UDP | STUN (NAT traversal) | ⚠️ Recomendado |
| **80** | TCP | Detección de portal cautivo (opcional) | ❌ No |

### Puertos Entrantes (Inbound)
- **UDP 41641** (o el puerto configurado): Para conexiones directas peer-to-peer
- Si se usa **peer relay**, el puerto UDP asignado debe estar abierto

## Problemas Comunes que Bloquean Tailscale

### 1. Firewall Bloqueando UDP 41641
**Síntoma:** Tailscale se conecta pero solo usa DERP (relays), no conexiones directas.
**Solución:** Permitir tráfico UDP saliente desde puerto fuente 41641 hacia cualquier destino.

### 2. Firewall Bloqueando TCP 443
**Síntoma:** Tailscale no puede iniciar sesión o conectarse al control plane.
**Solución:** Permitir tráfico TCP saliente al puerto 443.

### 3. NAT Restrictivo o Firewall con Deep Packet Inspection
**Síntoma:** Conexiones intermitentes o fallos de conexión.
**Solución:** 
- Deshabilitar bloqueo de P2P/VPN en el firewall
- Deshabilitar inspección profunda de paquetes (DPI) para tráfico Tailscale
- Permitir respuestas a conexiones UDP salientes (stateful firewall)

### 4. Dispositivo TUN/TAP No Disponible
**Síntoma:** Error "cannot create TUN device" o "Protocol not supported".
**Solución:** 
- Verificar que `/dev/net/tun` existe
- Cargar módulo `tun`: `sudo modprobe tun`
- Si el módulo no existe, el kernel no tiene soporte TUN compilado
- **Solicitar al proveedor:** Habilitar `CONFIG_TUN` en el kernel

### 5. Módulos del Kernel WireGuard No Disponibles
**Síntoma:** Error al iniciar Tailscale, fallos de conexión, o uso forzado de userspace mode.
**Solución:** 
- Verificar versión del kernel: `uname -r` (debe ser >= 5.6 para soporte nativo)
- Cargar módulo: `sudo modprobe wireguard`
- Si falla, instalar `wireguard-linux-compat` o actualizar kernel
- **Solicitar al proveedor:** 
  - Actualizar a kernel >= 5.6, O
  - Compilar kernel con `CONFIG_WIREGUARD=y` o `CONFIG_WIREGUARD=m`

### 6. Permisos Insuficientes
**Síntoma:** Error "permission denied" al crear interfaces de red.
**Solución:** 
- `tailscaled` debe ejecutarse como root o con `CAP_NET_ADMIN`
- Verificar: `getcap $(which tailscaled)`

## Información para el Proveedor

### Preguntas Específicas

1. **¿El firewall del servidor bloquea tráfico UDP saliente?**
   - Específicamente: ¿está bloqueado el puerto UDP 41641 saliente?
   - ¿Hay restricciones en puertos efímeros UDP?

2. **¿El firewall bloquea tráfico TCP saliente al puerto 443?**
   - Tailscale necesita HTTPS (443) para comunicarse con sus servidores de control.

3. **¿Hay políticas de bloqueo de P2P o VPN?**
   - Algunos firewalls corporativos bloquean automáticamente tráfico P2P/VPN.
   - ¿Se puede crear una excepción para Tailscale?

4. **¿El firewall tiene Deep Packet Inspection (DPI) activo?**
   - El DPI puede interferir con el tráfico WireGuard de Tailscale.
   - ¿Se puede deshabilitar o crear una excepción?

5. **¿Qué tipo de NAT está configurado?**
   - NAT restrictivo puede impedir conexiones peer-to-peer.
   - ¿Se puede configurar NAT menos restrictivo o port forwarding?

6. **¿Hay restricciones de ancho de banda o QoS que puedan afectar?**
   - Tailscale necesita latencia baja para conexiones directas.

7. **¿El kernel tiene soporte para TUN/TAP?**
   - **CRÍTICO:** Verificar que el módulo `tun` está disponible: `modprobe tun`
   - Verificar que existe `/dev/net/tun`
   - Si falla, el kernel no tiene `CONFIG_TUN` habilitado
   - **Solicitar:** Habilitar módulo TUN en el kernel

8. **¿El kernel tiene soporte para WireGuard?**
   - **CRÍTICO:** Verificar versión del kernel: `uname -r` (debe ser >= 5.6)
   - Verificar módulo: `modprobe wireguard`
   - Si falla, el kernel no tiene `CONFIG_WIREGUARD` habilitado
   - **Solicitar:** 
     - Actualizar a kernel >= 5.6, O
     - Compilar kernel con `CONFIG_WIREGUARD=y` o `CONFIG_WIREGUARD=m`

### Comandos de Diagnóstico (Ejecutar en el Servidor APS)

**⚠️ IMPORTANTE: Ejecutar primero los comandos del kernel antes de los de red**

```bash
# ============================================
# 1. DIAGNÓSTICO DEL KERNEL (CRÍTICO)
# ============================================

# Verificar versión del kernel
uname -r

# Verificar dispositivo TUN
ls -l /dev/net/tun

# Verificar módulo TUN
lsmod | grep tun
sudo modprobe tun && echo "✅ TUN disponible" || echo "❌ TUN NO disponible"

# Verificar módulo WireGuard
lsmod | grep wireguard
sudo modprobe wireguard && echo "✅ WireGuard disponible" || echo "❌ WireGuard NO disponible"

# Verificar configuración del kernel (si está disponible)
if [ -f /proc/config.gz ]; then
    echo "=== Configuración del Kernel ==="
    zgrep -E "CONFIG_TUN|CONFIG_WIREGUARD" /proc/config.gz
elif [ -f /boot/config-$(uname -r) ]; then
    echo "=== Configuración del Kernel ==="
    grep -E "CONFIG_TUN|CONFIG_WIREGUARD" /boot/config-$(uname -r)
fi

# ============================================
# 2. DIAGNÓSTICO DE TAILSCALE
# ============================================

# Verificar estado de Tailscale
sudo tailscale status

# Verificar conectividad UDP (MUY IMPORTANTE)
sudo tailscale netcheck

# Verificar logs de Tailscale
sudo journalctl -u tailscaled -n 50

# Verificar si hay errores relacionados con TUN
sudo journalctl -u tailscaled | grep -i "tun\|wireguard\|permission"

# ============================================
# 3. DIAGNÓSTICO DE RED
# ============================================

# Verificar conectividad al control plane
curl -v https://login.tailscale.com

# Verificar puertos UDP locales
sudo netstat -ulnp | grep 41641

# Verificar firewall (si es iptables)
sudo iptables -L -n -v | grep -E "41641|443"

# Verificar firewall (si es firewalld)
sudo firewall-cmd --list-all

# Verificar firewall (si es ufw)
sudo ufw status verbose
```

### Resultado Esperado de `tailscale netcheck`

Un diagnóstico saludable debería mostrar:
```
UDP: true
IPv4: yes, [IP pública]
IPv6: no
MappingVariesByDestIP: false
HairPinning: false
PortMapping: UPnP, ...
PreferredDERP: [DERP server]
DERPLatency: {
  "[DERP]": [latencia en ms]
}
```

Si muestra `UDP: false`, significa que el tráfico UDP está bloqueado.

## Soluciones Alternativas

### Solución 1: Modo Userspace (Si falta TUN/WireGuard)

Si el kernel no tiene soporte TUN o WireGuard, Tailscale puede usar modo userspace (menos eficiente):

```bash
# Detener tailscaled
sudo systemctl stop tailscaled

# Iniciar en modo userspace
sudo tailscaled --tun=userspace-networking

# O configurar permanentemente en /etc/default/tailscaled
# FLAGS="--tun=userspace-networking"
```

**Nota:** 
- Funciona pero con mayor uso de CPU y latencia
- Algunas características pueden no estar disponibles
- **No es recomendado para producción**

### Solución 2: Usar DERP (Relays) - Si falta conectividad UDP

Si no se pueden abrir los puertos UDP, Tailscale puede funcionar usando solo DERP (relays), pero con mayor latencia:

```bash
# Forzar uso de DERP
sudo tailscale up --accept-routes --advertise-routes=0.0.0.0/0
```

**Nota:** Esto funcionará pero con mayor latencia y menor rendimiento que conexiones directas.

## Configuración Recomendada para el Proveedor

### Requisitos del Kernel (CRÍTICO - Prioridad Alta)

1. **Habilitar módulo TUN:**
   - El kernel debe tener `CONFIG_TUN=y` (built-in) o `CONFIG_TUN=m` (módulo)
   - Verificar: `modprobe tun` debe funcionar
   - Si no está disponible, recompilar kernel con TUN habilitado

2. **Habilitar soporte WireGuard:**
   - **Opción A (Recomendada):** Actualizar a kernel >= 5.6 (WireGuard incluido)
   - **Opción B:** Compilar kernel con `CONFIG_WIREGUARD=y` o `CONFIG_WIREGUARD=m`
   - **Opción C:** Instalar módulo `wireguard-linux-compat` para kernels < 5.6
   - Verificar: `modprobe wireguard` debe funcionar

3. **Asegurar que `/dev/net/tun` existe:**
   - Debe existir el dispositivo: `/dev/net/tun`
   - Permisos: `crw-rw-rw-` (666)
   - Si no existe, crear: `mknod /dev/net/tun c 10 200`

### Reglas de Firewall a Aplicar

1. **Permitir tráfico UDP saliente:**
   - Puerto fuente: 41641 (o cualquier puerto efímero)
   - Puerto destino: Cualquiera
   - Protocolo: UDP
   - Dirección: Saliente (OUT)

2. **Permitir tráfico TCP saliente:**
   - Puerto destino: 443
   - Protocolo: TCP
   - Dirección: Saliente (OUT)

3. **Permitir tráfico UDP entrante (para conexiones directas):**
   - Puerto: 41641 (o el configurado)
   - Protocolo: UDP
   - Dirección: Entrante (IN)

4. **Permitir respuestas a conexiones establecidas:**
   - Estado: ESTABLISHED, RELATED
   - Protocolo: UDP, TCP

### Excepciones Específicas

- **IPs de Tailscale:** Permitir tráfico hacia/hacia `100.64.0.0/10` (rango de Tailscale)
- **Servidores DERP:** Permitir tráfico hacia los servidores DERP de Tailscale (lista disponible en su documentación)

## Referencias Técnicas

- [Tailscale Firewall Ports](https://tailscale.com/kb/1082/firewall-ports)
- [Tailscale Firewalls Guide](https://tailscale.com/kb/1181/firewalls/)
- [Tailscale Troubleshooting](https://tailscale.com/kb/1023/troubleshooting)

## Información del Servidor

- **Servidor APS:** 200.35.159.44
- **Servidor Local:** 100.77.240.103 (funciona correctamente con Tailscale)
- **Rango Tailscale:** 100.64.0.0/10
- **Puerto por defecto:** UDP 41641

---

**Fecha:** $(date +%Y-%m-%d)
**Contacto:** [Tu información de contacto]
