# Guía de Despliegue Público - Minecraft Admin Panel

## 📋 Resumen

Esta guía explica cómo:
1. Exponer el panel en `admin-minecraft.castbar.dev`
2. Configurar múltiples servidores remotos (como `cobblemon.castbar.dev` y otros fuera de tu espacio)

## 🏗️ Arquitectura

```
Internet
   ↓
admin-minecraft.castbar.dev (AWS - 56.126.122.151)
   ↓ (Reverse Proxy: Nginx/Traefik)
   ↓
Panel Django (Backend API) + Frontend Ionic
   ↓ (RCON sobre Internet/Tailscale)
   ↓
Servidores Minecraft Remotos:
   - cobblemon.castbar.dev (IP: X.X.X.X, RCON: 25575)
   - Otro servidor (IP: Y.Y.Y.Y, RCON: 25575)
   - Servidor local (100.77.240.103, RCON: 25575)
```

## ✅ Lo que ya funciona

El sistema **YA soporta servidores remotos** porque:
- El modelo `Server` tiene campo `host` que acepta IP o dominio
- RCON se conecta usando `server.host` y `server.rcon_port` (no requiere Docker)
- No necesita que el servidor esté en la misma red Docker

## 🚀 Paso 1: Configurar Reverse Proxy en AWS

### Opción A: Usar Nginx en AWS (Recomendado)

1. **Instalar Nginx en el servidor AWS:**
```bash
ssh ubuntu@56.126.122.151
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx
```

2. **Crear configuración de Nginx:**
```bash
sudo nano /etc/nginx/sites-available/admin-minecraft.castbar.dev
```

```nginx
server {
    listen 80;
    server_name admin-minecraft.castbar.dev;
    
    # Redirigir a HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name admin-minecraft.castbar.dev;
    
    # Certificados SSL (se generan con certbot)
    ssl_certificate /etc/letsencrypt/live/admin-minecraft.castbar.dev/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/admin-minecraft.castbar.dev/privkey.pem;
    
    # Configuración SSL moderna
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Headers de seguridad
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Permitir archivos grandes (para backups)
    client_max_body_size 2G;
    
    # Proxy al servidor local (vía Tailscale)
    location / {
        proxy_pass http://100.77.240.103:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        
        # Timeouts aumentados para backups grandes
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
        
        # WebSocket support (si se necesita en el futuro)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

3. **Habilitar el sitio:**
```bash
sudo ln -s /etc/nginx/sites-available/admin-minecraft.castbar.dev /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

4. **Configurar SSL con Let's Encrypt:**
```bash
sudo certbot --nginx -d admin-minecraft.castbar.dev
```

### Opción B: Usar Traefik (Si ya lo tienes configurado)

Si ya usas Traefik en AWS, agrega estas labels al contenedor:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.minecraft-admin.rule=Host(`admin-minecraft.castbar.dev`)"
  - "traefik.http.routers.minecraft-admin.entrypoints=websecure"
  - "traefik.http.routers.minecraft-admin.tls.certresolver=letsencrypt"
  - "traefik.http.services.minecraft-admin.loadbalancer.server.port=8080"
```

## 🔧 Paso 2: Configurar DNS

1. **Agregar registro DNS:**
   - Tipo: `A`
   - Nombre: `admin-minecraft`
   - Valor: `56.126.122.151` (IP del servidor AWS)
   - TTL: 300

2. **Verificar DNS:**
```bash
dig admin-minecraft.castbar.dev
# Debe apuntar a 56.126.122.151
```

## ⚙️ Paso 3: Ajustar Configuración Django

Actualizar `panel/minecraft_panel/settings.py`:

```python
# ALLOWED_HOSTS - Agregar el dominio público
ALLOWED_HOSTS = [
    'admin-minecraft.castbar.dev',
    '100.77.240.103',  # IP local (Tailscale)
    'localhost',
    '127.0.0.1',
]

# CSRF Trusted Origins - Agregar el dominio con HTTPS
CSRF_TRUSTED_ORIGINS = [
    'https://admin-minecraft.castbar.dev',
    'http://localhost:8080',
    'http://localhost:4200',
    'http://localhost:8100',
]

# CORS - Permitir el dominio público
CORS_ALLOWED_ORIGINS = [
    'https://admin-minecraft.castbar.dev',
    'http://localhost:4200',
    'http://localhost:8100',
    'http://localhost:8080',
]

# SITE_URL - Actualizar para emails y links
SITE_URL = os.environ.get('SITE_URL', 'https://admin-minecraft.castbar.dev')
```

## 🔐 Paso 4: Configurar Servidores Remotos

### Para servidores en la misma red (Tailscale)

1. **Acceder al panel:** `https://admin-minecraft.castbar.dev`
2. **Ir a Admin Django:** `https://admin-minecraft.castbar.dev/admin/`
3. **Agregar servidor:**
   - **Name:** `Cobblemon Server`
   - **Host:** `cobblemon.castbar.dev` o `100.77.240.103` (IP Tailscale)
   - **Container name:** `cobblemon-server` (opcional, solo si está en Docker local)
   - **Port:** `25565` (puerto del juego)
   - **RCON Port:** `25575`
   - **RCON Password:** `[contraseña RCON]`
   - **Minecraft Data Path:** `/data`
   - **Auth Mode:** `whitelist`
   - **Whitelist Enabled:** ✅

### Para servidores remotos (fuera de tu espacio)

1. **Requisitos del servidor remoto:**
   - RCON debe estar habilitado en `server.properties`:
     ```
     enable-rcon=true
     rcon.port=25575
     rcon.password=tu_contraseña_segura
     ```
   - El puerto RCON debe estar **expuesto y accesible** desde internet o VPN
   - Si está detrás de un firewall, abrir el puerto RCON (25575 TCP)

2. **Agregar servidor remoto en el panel:**
   - **Name:** `Servidor Remoto X`
   - **Host:** `IP_PUBLICA` o `dominio.com` (donde esté el servidor)
   - **Container name:** (dejar vacío, no aplica para servidores remotos)
   - **Port:** `25565`
   - **RCON Port:** `25575` (o el puerto que uses)
   - **RCON Password:** `[contraseña RCON del servidor remoto]`
   - **Minecraft Data Path:** `/data` (no se usa para servidores remotos, solo para backups locales)
   - **Auth Mode:** `whitelist` o `database`
   - **Whitelist Enabled:** ✅

3. **Verificar conectividad RCON:**
```bash
# Desde el servidor AWS o local, probar conexión RCON
telnet IP_SERVIDOR_REMOTO 25575
# O usar mcrcon
mcrcon -H IP_SERVIDOR_REMOTO -P 25575 -p PASSWORD "list"
```

## 🔒 Paso 5: Seguridad

### Firewall en Servidores Remotos

Si el servidor remoto tiene firewall, permitir conexiones RCON solo desde:
- IP del servidor AWS: `56.126.122.151`
- IP del servidor local: `100.77.240.103`
- O mejor: usar Tailscale VPN para todos los servidores

### Ejemplo con UFW (Ubuntu):
```bash
# En el servidor remoto
sudo ufw allow from 56.126.122.151 to any port 25575 proto tcp
sudo ufw allow from 100.77.240.103 to any port 25575 proto tcp
```

### Mejor: Usar Tailscale para todos los servidores

1. **Instalar Tailscale en servidor remoto:**
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

2. **Usar IP de Tailscale en el panel:**
   - **Host:** `100.X.X.X` (IP Tailscale del servidor remoto)
   - Así el RCON no está expuesto a internet

## 📝 Paso 6: Probar Configuración

1. **Acceder al panel:**
   ```
   https://admin-minecraft.castbar.dev
   ```

2. **Verificar que se ven los servidores:**
   - Debe mostrar todos los servidores configurados
   - Tanto locales como remotos

3. **Probar funcionalidades:**
   - ✅ Ver estado del servidor
   - ✅ Listar jugadores
   - ✅ Agregar a whitelist
   - ✅ Ejecutar comandos RCON
   - ⚠️ Backups: Solo funcionan para servidores locales (Docker)
   - ⚠️ Control Docker: Solo para servidores locales

## ⚠️ Limitaciones

### Funcionalidades que SOLO funcionan con servidores locales (Docker):
- ✅ Backups automáticos (requiere acceso a Docker)
- ✅ Control de contenedor (start/stop/restart)
- ✅ Logs del servidor (lectura de archivos)
- ✅ Gestión de mods (acceso a sistema de archivos)

### Funcionalidades que funcionan con servidores remotos:
- ✅ Gestión de whitelist (vía RCON)
- ✅ Ejecutar comandos (vía RCON)
- ✅ Ver jugadores online (vía RCON)
- ✅ Ver estado del servidor (vía RCON)
- ✅ Gestión de usuarios de Minecraft (si usa modo database)

## 🔄 Actualizar Configuración Existente

Si ya tienes el panel corriendo localmente:

1. **Actualizar settings.py** (como se indicó arriba)
2. **Reiniciar contenedores:**
```bash
cd /ruta/al/proyecto
docker compose restart minecraft-admin-panel
```

3. **Verificar logs:**
```bash
docker logs minecraft-admin-panel --tail 50
```

## 📊 Resumen de Configuración

| Componente | Valor |
|------------|-------|
| **Panel URL** | `https://admin-minecraft.castbar.dev` |
| **Backend Django** | `100.77.240.103:8000` (vía Tailscale) |
| **Frontend** | `100.77.240.103:8080` (vía Tailscale) |
| **Reverse Proxy** | `56.126.122.151` (AWS) |
| **Servidores Remotos** | Se conectan vía RCON (IP pública o Tailscale) |

## 🆘 Troubleshooting

### Error: "Cannot connect to RCON"
- Verificar que RCON está habilitado en `server.properties`
- Verificar que el puerto RCON está abierto en el firewall
- Probar conexión manual: `mcrcon -H IP -P PORT -p PASSWORD "list"`

### Error: "CSRF verification failed"
- Verificar que `CSRF_TRUSTED_ORIGINS` incluye `https://admin-minecraft.castbar.dev`
- Verificar que el proxy pasa los headers correctos

### Error: "DisallowedHost"
- Verificar que `ALLOWED_HOSTS` incluye `admin-minecraft.castbar.dev`
- Reiniciar el contenedor Django

### Los backups no funcionan para servidores remotos
- **Es normal**: Los backups requieren acceso a Docker y sistema de archivos
- Para servidores remotos, usar backups nativos del servidor o scripts externos

## 📚 Referencias

- [Documentación RCON](https://wiki.vg/RCON)
- [Nginx Reverse Proxy](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)
- [Let's Encrypt](https://letsencrypt.org/)
