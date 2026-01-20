# Configuración Nginx Proxy Manager - Castbar

## 📋 Resumen

Nginx Proxy Manager está configurado en el servidor local (castbar - 100.77.240.103) y gestiona todas las comunicaciones entre el servidor APS y el servidor local a través de la VPN Tailscale.

## 🌐 Información de Red

| Servidor | IP Tailscale | IP Pública | Descripción |
|----------|------------|------------|-------------|
| **castbar** (local) | 100.77.240.103 | - | Servidor donde corre Nginx Proxy Manager |
| **aps** | 100.73.189.54 | 200.35.159.44 | Servidor público (AWS) |

## 🚀 Estado Actual

- ✅ Nginx Proxy Manager corriendo en `100.77.240.103:81`
- ✅ Conectividad Tailscale verificada entre servidores
- ✅ Contenedor puede acceder a servicios en servidor APS vía Tailscale

## 🔐 Acceso al Panel

### Credenciales por Defecto
- **Email:** `admin@example.com`
- **Password:** `changeme`

⚠️ **IMPORTANTE:** Cambiar estas credenciales después del primer login.

### URLs de Acceso
- **Vía Tailscale:** `http://100.77.240.103:81`
- **Desde servidor local:** `http://localhost:81`
- **Dominio (a configurar):** `https://proxy-manager.castbar.dev`

## 📝 Configuración del Dominio proxy-manager.castbar.dev

### Paso 1: Configurar DNS

El dominio `proxy-manager.castbar.dev` debe apuntar a la **IP pública del servidor APS** (200.35.159.44).

**Configuración DNS:**

En tu proveedor de DNS (donde está configurado castbar.dev), crear un registro:

- **Tipo:** `A` (no CNAME)
- **Nombre/Host:** `proxy-manager`
- **Valor/Dirección:** `200.35.159.44`
- **TTL:** `3600` (o el valor por defecto)

**Ejemplo de configuración:**
```
Tipo: A
Host: proxy-manager
Valor: 200.35.159.44
TTL: 3600
```

Esto creará el subdominio: `proxy-manager.castbar.dev` → `200.35.159.44`

**¿Por qué registro A y no CNAME?**
- Los registros A apuntan directamente a una IP
- Los CNAME apuntan a otro nombre de dominio
- En este caso, necesitamos apuntar directamente a la IP del servidor APS
- Es más rápido y eficiente que un CNAME

### Paso 2: Configurar Nginx en el Servidor APS

✅ **Ya configurado automáticamente**

El archivo `/etc/nginx/sites-available/proxy-manager` ya está creado y configurado para:
- Hacer proxy hacia `100.77.240.103:81` (NPM en servidor local) vía Tailscale
- Redirigir HTTP a HTTPS
- Soporte para WebSockets (necesario para NPM)

### Paso 3: Configurar SSL con Certbot

Después de configurar el DNS (puede tardar unos minutos en propagarse), obtener el certificado SSL:

```bash
ssh root@200.35.159.44
certbot --nginx -d proxy-manager.castbar.dev
```

Esto:
- Obtendrá el certificado SSL de Let's Encrypt
- Configurará automáticamente nginx para usar HTTPS
- Habilitará redirección HTTP → HTTPS

### Paso 4: Verificar

```bash
# Desde cualquier máquina con acceso a internet
curl -I https://proxy-manager.castbar.dev
```

Debería retornar un código 200 y mostrar los headers de Nginx Proxy Manager.

## 🔄 Configurar Proxies hacia Servicios en el Servidor APS

Para crear proxies que apunten a servicios en el servidor APS usando Tailscale:

### Ejemplo: Proxy para un servicio en el APS

1. En NPM, ir a **Proxy Hosts** → **Add Proxy Host**
2. Configurar:
   - **Domain Names:** `servicio.castbar.dev` (ejemplo)
   - **Scheme:** `http` o `https` (según el servicio)
   - **Forward Hostname/IP:** `100.73.189.54` (IP Tailscale del APS)
   - **Forward Port:** `[PUERTO_DEL_SERVICIO]` (ej: 80, 443, 8080, etc.)
   - **Block Common Exploits:** ✅ Activado
   - **Websockets Support:** ✅ Activado (si el servicio lo requiere)
3. Configurar SSL (si es necesario)
4. Guardar

### Ventajas de usar IP Tailscale

- ✅ Comunicación directa entre servidores (sin pasar por internet pública)
- ✅ Mayor seguridad (tráfico encriptado por WireGuard)
- ✅ No consume ancho de banda público
- ✅ Latencia más baja (aunque el túnel inverso puede ser más rápido)

## 🔧 Comandos Útiles

### Verificar estado de NPM
```bash
ssh carlitos@100.77.240.103
cd ~/nginx-proxy-manager
docker compose ps
```

### Ver logs de NPM
```bash
docker logs nginx-proxy-manager --tail 50 -f
```

### Reiniciar NPM
```bash
cd ~/nginx-proxy-manager
docker compose restart
```

### Verificar conectividad Tailscale desde contenedor
```bash
docker exec nginx-proxy-manager curl -I http://100.73.189.54:80
```

### Verificar conectividad Tailscale desde servidor
```bash
ping -c 3 100.73.189.54
curl -I http://100.73.189.54:80
```

## 📊 Arquitectura

```
Internet
   │
   ├─→ proxy-manager.castbar.dev (DNS)
   │         │
   │         └─→ [Túnel Inverso o IP Pública]
   │                   │
   │                   └─→ Servidor Local (100.77.240.103)
   │                             │
   │                             ├─→ Nginx Proxy Manager (Puerto 81)
   │                             │
   │                             └─→ Tailscale VPN (100.77.240.103)
   │                                       │
   │                                       └─→ Servidor APS (100.73.189.54)
   │                                                 │
   │                                                 └─→ Servicios en APS
```

## 🔒 Seguridad

### Recomendaciones

1. **Cambiar credenciales por defecto** inmediatamente después del primer login
2. **Habilitar 2FA** en NPM si está disponible
3. **Usar SSL/TLS** para todos los dominios públicos
4. **Configurar firewall** para limitar acceso al puerto 81 solo desde Tailscale
5. **Mantener NPM actualizado** regularmente

### Firewall (Opcional)

Para restringir el acceso al panel solo desde Tailscale:

```bash
# Permitir acceso solo desde red Tailscale (100.64.0.0/10)
sudo ufw allow from 100.64.0.0/10 to any port 81
sudo ufw deny 81
```

## 🐛 Troubleshooting

### El contenedor no puede acceder a servicios en APS

1. Verificar conectividad Tailscale:
   ```bash
   ping 100.73.189.54
   ```

2. Verificar que el servicio esté escuchando en el APS:
   ```bash
   ssh root@200.35.159.44 'netstat -tlnp | grep [PUERTO]'
   ```

3. Verificar firewall en el APS:
   ```bash
   ssh root@200.35.159.44 'ufw status'
   ```

### El dominio no resuelve

1. Verificar DNS:
   ```bash
   dig proxy-manager.castbar.dev
   nslookup proxy-manager.castbar.dev
   ```

2. Verificar que el túnel inverso esté funcionando (si aplica)

3. Verificar logs de NPM:
   ```bash
   docker logs nginx-proxy-manager --tail 100
   ```

### Error de SSL/Let's Encrypt

1. Verificar que el dominio apunte correctamente
2. Verificar que los puertos 80 y 443 estén abiertos
3. Verificar logs de Let's Encrypt:
   ```bash
   docker logs nginx-proxy-manager | grep -i "letsencrypt\|ssl\|certificate"
   ```

## 📚 Referencias

- [Nginx Proxy Manager Documentation](https://nginxproxymanager.com/guide/)
- [Tailscale Documentation](https://tailscale.com/kb/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)

---

**Última actualización:** 2026-01-19
**Servidor:** castbar (100.77.240.103)
**Versión NPM:** Latest (jc21/nginx-proxy-manager:latest)
