# Guía: Gestión de Servidores Remotos y Usuarios

## 📋 Resumen

Esta guía explica:
1. Cómo agregar servidores remotos (ej: `panel.castbar.dev`)
2. Sistema de usuarios y permisos
3. Quién puede crear servidores
4. Cómo configurar usuarios para acceder al panel

## 🖥️ Agregar un Servidor Remoto

### Escenario: Servidor en `panel.castbar.dev`

El panel **YA soporta servidores remotos**. Solo necesitas:

1. **Acceder al Admin Django:** `https://admin-minecraft.castbar.dev/admin/`
2. **Ir a:** `Servers` → `Add Server`
3. **Configurar:**
   - **Name:** `Panel Castbar Server` (o el nombre que quieras)
   - **Host:** `panel.castbar.dev` (o la IP pública del servidor)
   - **Container name:** (dejar vacío para servidores remotos)
   - **Port:** `25565` (puerto del juego)
   - **RCON Port:** `25575` (o el puerto RCON que uses)
   - **RCON Password:** `[contraseña RCON del servidor remoto]`
   - **Minecraft Data Path:** `/data` (no se usa para remotos, solo para backups locales)
   - **Auth Mode:** `whitelist`, `database`, o `both`
   - **Whitelist Enabled:** ✅

### Requisitos del Servidor Remoto

El servidor remoto debe tener:

1. **RCON habilitado** en `server.properties`:
   ```
   enable-rcon=true
   rcon.port=25575
   rcon.password=tu_contraseña_segura
   ```

2. **Puerto RCON accesible:**
   - Si está en internet: abrir puerto `25575` TCP en el firewall
   - Si está en VPN (Tailscale): usar IP de Tailscale como `host`
   - Recomendado: usar Tailscale para mayor seguridad

3. **Conectividad de red:**
   - El panel debe poder conectarse al servidor remoto vía RCON
   - Probar: `mcrcon -H panel.castbar.dev -P 25575 -p PASSWORD "list"`

### Ejemplo: Agregar Servidor Remoto

```bash
# Desde el panel (Admin Django o API)
POST /api/servers/create/
Headers: 
  - Cookie: sessionid=...
Body:
{
  "name": "Panel Castbar Server",
  "host": "panel.castbar.dev",
  "rcon_port": 25575,
  "rcon_password": "ContraseñaSegura123!@#",
  "port": 25565,
  "auth_mode": "whitelist",
  "enable_whitelist": true
}
```

**Nota:** Solo usuarios con `is_staff=True` pueden crear servidores.

## 👥 Sistema de Usuarios

### Tipos de Usuarios

#### 1. **Usuarios Django** (Acceso al Panel Web)
- Se autentican en `https://admin-minecraft.castbar.dev`
- Gestionan servidores desde el panel web
- **NO hay registro público** - solo los crea un admin/staff

#### 2. **Usuarios de Minecraft** (Jugadores en el Servidor)
- Se autentican en el servidor Minecraft (no en el panel)
- Solo si el servidor usa `auth_mode='database'` o `'both'`
- Se crean desde el panel por un admin

### Permisos y Roles

#### Roles en el Panel (UserServerRole):

| Rol | Permisos |
|-----|----------|
| **admin** | Todo: ver, whitelist, mods, control, logs, comandos, usuarios, configuración |
| **moderator** | Ver, whitelist, logs, comandos |
| **viewer** | Solo ver y logs |

#### Permisos Especiales:

- **`is_staff=True`**: Puede crear servidores y gestionar usuarios Django
- **`is_superuser=True`**: Acceso completo al admin Django

## 🔐 ¿Quién Puede Crear Servidores?

### ❌ NO: Cualquiera NO puede crear servidores

**Solo usuarios con `is_staff=True` pueden:**
- Crear nuevos servidores (`POST /api/servers/create/`)
- Gestionar usuarios Django
- Acceder a funciones administrativas

### ✅ SÍ: Cualquier usuario autenticado puede:
- Ver servidores a los que tiene acceso (según `UserServerRole`)
- Gestionar whitelist (si tiene rol `admin` o `moderator`)
- Ejecutar comandos (si tiene acceso al servidor)
- Ver logs (si tiene acceso al servidor)

## 📝 Flujo de Configuración de Usuarios

### Escenario 1: Agregar Usuario para Acceder al Panel

1. **Admin/Staff crea usuario Django:**
   ```
   POST /api/users/create/
   Body: {
     "username": "nuevo_usuario",
     "email": "usuario@ejemplo.com",
     "password": "contraseña_segura",
     "is_staff": false,  // false = usuario normal
     "is_active": true
   }
   ```

2. **Asignar acceso a servidor:**
   ```
   POST /api/servers/{server_id}/roles/assign/
   Body: {
     "user_id": 2,
     "role": "admin"  // o "moderator", "viewer"
   }
   ```

3. **Usuario puede:**
   - Hacer login en `https://admin-minecraft.castbar.dev`
   - Ver y gestionar el servidor según su rol

### Escenario 2: Agregar Jugador de Minecraft

1. **Admin crea usuario de Minecraft:**
   ```
   POST /api/servers/{server_id}/users/create/
   Body: {
     "username": "jugador123",
     "password": "password123",
     "email": "jugador@ejemplo.com"  // opcional
   }
   ```

2. **Jugador se conecta al servidor:**
   - El plugin/mod del servidor valida con el panel
   - Si las credenciales son correctas, puede entrar

## 🏗️ Arquitectura Multi-Servidor

```
admin-minecraft.castbar.dev (Panel Central)
    ↓
    ├── Servidor Local (100.77.240.103)
    │   └── cobblemon-server (Docker local)
    │
    ├── Servidor Remoto 1 (panel.castbar.dev)
    │   └── Conexión RCON vía Internet/VPN
    │
    └── Servidor Remoto 2 (otro-servidor.com)
        └── Conexión RCON vía Internet/VPN
```

### Ventajas:
- ✅ Panel centralizado para múltiples servidores
- ✅ Un solo login para gestionar todos los servidores
- ✅ Roles y permisos por servidor
- ✅ No requiere que los servidores estén en la misma red

## 🔧 Ejemplo Práctico: Agregar Servidor Remoto

### Paso 1: Preparar el Servidor Remoto

En `panel.castbar.dev`:

```bash
# Habilitar RCON en server.properties
enable-rcon=true
rcon.port=25575
rcon.password=MiContraseñaSegura2024!@#

# Abrir puerto en firewall (si es necesario)
sudo ufw allow from 56.126.122.151 to any port 25575 proto tcp
# O mejor: usar Tailscale
```

### Paso 2: Agregar en el Panel

**Opción A: Desde Admin Django**
1. Ir a: `https://admin-minecraft.castbar.dev/admin/server/server/add/`
2. Llenar formulario con datos del servidor remoto
3. Guardar

**Opción B: Desde API**
```bash
curl -X POST https://admin-minecraft.castbar.dev/api/servers/create/ \
  -H "Cookie: sessionid=..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Panel Castbar Server",
    "host": "panel.castbar.dev",
    "rcon_port": 25575,
    "rcon_password": "MiContraseñaSegura2024!@#",
    "port": 25565
  }'
```

### Paso 3: Asignar Usuarios

1. **Crear usuario Django** (si no existe):
   ```
   POST /api/users/create/
   {
     "username": "admin_panel",
     "password": "contraseña",
     "is_staff": true
   }
   ```

2. **Asignar acceso al servidor:**
   ```
   POST /api/servers/{server_id}/roles/assign/
   {
     "user_id": 2,
     "role": "admin"
   }
   ```

## 🚫 Limitaciones de Servidores Remotos

### ✅ Funciona con Servidores Remotos:
- Gestión de whitelist (vía RCON)
- Ejecutar comandos (vía RCON)
- Ver jugadores online (vía RCON)
- Ver estado del servidor (vía RCON)
- Gestión de usuarios de Minecraft (si usa modo database)

### ❌ NO Funciona con Servidores Remotos:
- Backups automáticos (requiere acceso a Docker y archivos)
- Control de contenedor (start/stop/restart - requiere Docker)
- Ver logs del servidor (requiere acceso a archivos)
- Gestión de mods (requiere acceso a sistema de archivos)

## 🔒 Seguridad

### Recomendaciones:

1. **Usar Tailscale para servidores remotos:**
   - Más seguro que exponer RCON a internet
   - Usar IP de Tailscale como `host`

2. **Contraseñas RCON seguras:**
   - Mínimo 20 caracteres
   - Mayúsculas, minúsculas, números, símbolos
   - No reutilizar contraseñas

3. **Firewall:**
   - Permitir RCON solo desde IPs conocidas
   - O mejor: solo vía Tailscale

4. **Usuarios del Panel:**
   - Solo crear usuarios de confianza
   - Usar `is_staff=True` solo para administradores
   - Asignar roles apropiados (admin/moderator/viewer)

## 📊 Resumen de Permisos

| Acción | Requisito |
|--------|-----------|
| Crear servidor | `is_staff=True` |
| Ver servidor | Tener `UserServerRole` en ese servidor |
| Gestionar whitelist | Rol `admin` o `moderator` |
| Ejecutar comandos | Tener acceso al servidor |
| Crear usuarios Django | `is_staff=True` |
| Asignar roles | `is_staff=True` o ser `admin` del servidor |
| Gestionar usuarios Minecraft | Rol `admin` del servidor |

## 🆘 Troubleshooting

### Error: "Permission denied: Only staff can create servers"
- **Solución:** El usuario necesita `is_staff=True`
- **Cómo:** Un superuser debe actualizar el usuario desde `/admin/auth/user/`

### Error: "Cannot connect to RCON"
- Verificar que RCON está habilitado en el servidor remoto
- Verificar que el puerto está abierto en el firewall
- Probar conexión manual: `mcrcon -H HOST -P PORT -p PASSWORD "list"`

### Error: "No access to this server"
- El usuario no tiene `UserServerRole` asignado
- **Solución:** Asignar rol desde `/admin/server/userserverrole/add/` o API
