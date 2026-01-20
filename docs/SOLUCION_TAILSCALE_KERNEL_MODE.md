# Solución: Habilitar Tailscale en Modo Kernel (Normal)

## 🔍 Problema Actual

El servidor APS está ejecutando Tailscale en **modo userspace** porque:
- Kernel 5.2.0 (Virtuozzo) no tiene soporte WireGuard nativo
- No se pueden compilar módulos del kernel desde dentro del contenedor Virtuozzo
- El módulo `wireguard-dkms` no se pudo compilar (faltan headers del kernel)

**Consecuencia:** Nginx no puede hacer proxy hacia IPs de Tailscale porque no hay interfaz de red tradicional.

## ✅ Soluciones Disponibles

### Opción 1: Solicitar al Proveedor Habilitar WireGuard (RECOMENDADA)

**Contactar al proveedor del servidor APS** y solicitar:

1. **Habilitar módulo WireGuard en el host:**
   ```bash
   # En el host (no en el contenedor)
   modprobe wireguard
   ```

2. **Instalar headers del kernel de Virtuozzo:**
   - Instalar `vzkernel-devel` o equivalente para kernel 5.2.0-1160.90.1.vz7.200.7
   - Compilar módulo WireGuard en el host
   - Cargar módulo en el host

3. **Verificar que el módulo esté disponible:**
   ```bash
   # Desde el contenedor
   lsmod | grep wireguard
   modprobe wireguard
   ```

**Ventajas:**
- ✅ Tailscale funcionará en modo kernel (más rápido)
- ✅ Nginx podrá hacer proxy hacia IPs de Tailscale
- ✅ Mejor rendimiento y menor latencia

**Desventajas:**
- ⏳ Requiere intervención del proveedor
- ⏳ Puede tardar días en implementarse

---

### Opción 2: Usar Nombre de Host de Tailscale (SOLUCIÓN TEMPORAL)

Tailscale resuelve automáticamente los nombres de host. Podemos usar el nombre en lugar de la IP:

**Modificar configuración de nginx:**

```bash
ssh root@200.35.159.44

# Editar configuración
nano /etc/nginx/sites-available/proxy-manager
```

**Cambiar:**
```nginx
proxy_pass http://100.77.240.103:81/;
```

**Por:**
```nginx
proxy_pass http://castbar.ts.net:81/;
# O si no funciona, usar:
proxy_pass http://castbar:81/;
```

**Reiniciar nginx:**
```bash
nginx -t && systemctl reload nginx
```

**Ventajas:**
- ✅ Funciona inmediatamente
- ✅ No requiere cambios en el host
- ✅ Tailscale resuelve el nombre automáticamente

**Desventajas:**
- ⚠️ Depende de la resolución DNS de Tailscale
- ⚠️ Puede ser más lento que usar IP directa

---

### Opción 3: Túnel SSH como Proxy (ALTERNATIVA)

Si las opciones anteriores no funcionan, podemos usar un túnel SSH:

**En el servidor APS, crear túnel SSH:**
```bash
ssh -N -L 127.0.0.1:8181:100.77.240.103:81 carlitos@100.77.240.103
```

**Modificar nginx para usar el túnel local:**
```nginx
proxy_pass http://127.0.0.1:8181/;
```

**Ventajas:**
- ✅ Funciona sin cambios en el host
- ✅ No depende de Tailscale

**Desventajas:**
- ❌ Requiere mantener túnel SSH activo
- ❌ Más complejo de mantener
- ❌ Depende de conexión SSH

---

### Opción 4: Actualizar Kernel (SI ES POSIBLE)

Si el proveedor permite actualizar el kernel a >= 5.6:

```bash
# Verificar kernels disponibles
apt list --upgradable | grep linux-image

# Instalar kernel >= 5.6
apt install linux-image-5.15.0-generic linux-headers-5.15.0-generic

# Reiniciar servidor
reboot
```

**Después del reinicio:**
- WireGuard estará incluido en el kernel
- Tailscale funcionará en modo kernel automáticamente

**Ventajas:**
- ✅ Solución permanente
- ✅ Mejor rendimiento

**Desventajas:**
- ⚠️ Requiere reinicio del servidor
- ⚠️ Puede no ser posible en Virtuozzo

---

## 🚀 Implementación Recomendada

### Paso 1: Intentar Opción 2 (Inmediato)

```bash
ssh root@200.35.159.44

# Editar configuración
sed -i 's|http://100.77.240.103:81/|http://castbar.ts.net:81/|g' /etc/nginx/sites-available/proxy-manager

# Verificar
nginx -t

# Si la sintaxis es correcta, recargar
systemctl reload nginx

# Probar
curl -I -H "Host: proxy-manager.castbar.dev" http://localhost
```

### Paso 2: Contactar Proveedor (Paralelo)

Enviar solicitud al proveedor:

```
Asunto: Solicitud - Habilitar soporte WireGuard en host Virtuozzo

Estimados,

Necesito habilitar el módulo WireGuard en el host para que funcione 
correctamente en los contenedores.

Información del sistema:
- Kernel: 5.2.0-1160.90.1.vz7.200.7
- Virtuozzo Container

Solicito:
1. Instalar headers del kernel (vzkernel-devel o equivalente)
2. Compilar y cargar módulo WireGuard en el host
3. Verificar que el módulo esté disponible para los contenedores

Gracias.
```

### Paso 3: Verificar Funcionamiento

```bash
# Desde el servidor APS
modprobe wireguard
lsmod | grep wireguard

# Si funciona, reiniciar Tailscale
systemctl restart tailscaled

# Verificar modo
tailscale status
# Debe mostrar conexión directa, no "via DERP"
```

---

## 📊 Comparación de Opciones

| Opción | Velocidad | Complejidad | Tiempo | Recomendación |
|--------|-----------|-------------|--------|---------------|
| **Opción 1: Proveedor** | ⭐⭐⭐⭐⭐ | ⭐⭐ | Días | ✅ Mejor a largo plazo |
| **Opción 2: Nombre host** | ⭐⭐⭐⭐ | ⭐ | Inmediato | ✅ Mejor inmediato |
| **Opción 3: Túnel SSH** | ⭐⭐⭐ | ⭐⭐⭐ | Inmediato | ⚠️ Solo si otras fallan |
| **Opción 4: Actualizar kernel** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Horas | ⚠️ Si es posible |

---

## 🔧 Verificación Post-Implementación

Después de implementar cualquier solución:

```bash
# 1. Verificar que Tailscale esté en modo kernel
tailscale status
# Debe mostrar conexión directa, no "via DERP"

# 2. Verificar conectividad
ping -c 3 100.77.240.103
# Debe funcionar (no 100% packet loss)

# 3. Verificar que nginx pueda hacer proxy
curl -I http://100.77.240.103:81
# O si usas nombre:
curl -I http://castbar.ts.net:81

# 4. Verificar proxy completo
curl -I -H "Host: proxy-manager.castbar.dev" http://localhost
```

---

**Última actualización:** 2026-01-19
**Estado:** Pendiente implementación
