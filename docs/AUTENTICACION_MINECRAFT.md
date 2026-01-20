# Sistema de Autenticación con Usuario y Clave para Minecraft

## 📋 Resumen

El panel ya incluye un sistema de autenticación que permite que los jugadores se conecten al servidor usando usuario y contraseña gestionados desde el panel, en lugar de solo usar whitelist.

## 🔧 Componentes del Sistema

### 1. Backend (Django Panel)
- ✅ **Modelo `MinecraftUser`**: Almacena usuarios con contraseñas hasheadas
- ✅ **Endpoint de autenticación**: `/api/servers/{server_id}/auth/`
- ✅ **API de gestión**: Crear, actualizar, eliminar usuarios desde el panel
- ✅ **Modos de autenticación**: `whitelist`, `database`, `both`, `public`

### 2. Frontend (Panel Web)
- ✅ **Gestión de usuarios**: Crear y administrar usuarios desde la interfaz
- ✅ **Configuración de servidor**: Cambiar modo de autenticación

### 3. Plugin/Mod de Minecraft (Falta implementar)
- ❌ **Plugin Fabric**: Intercepta conexiones y valida contra el panel
- ❌ **Plugin Bukkit/Spigot**: Alternativa para servidores Paper/Spigot

## 🚀 Cómo Funciona

### Flujo de Autenticación

1. **Admin crea usuario en el panel**:
   ```
   POST /api/servers/{server_id}/users/create/
   {
     "username": "jonathan2837",
     "password": "mi_password_segura"
   }
   ```

2. **Jugador intenta conectarse al servidor**:
   - El plugin/mod intercepta la conexión
   - Solicita usuario y contraseña (en chat o mediante comando)
   - Valida contra el panel vía API

3. **Plugin valida credenciales**:
   ```
   POST /api/servers/{server_id}/auth/
   Headers: X-API-Key: {api_key_del_servidor}
   {
     "username": "jonathan2837",
     "password": "mi_password_segura"
   }
   ```

4. **Panel responde**:
   ```json
   {
     "valid": true,
     "username": "jonathan2837",
     "source": "database"
   }
   ```

5. **Plugin permite o rechaza la conexión** según la respuesta

## 📝 Configuración del Servidor

### Paso 1: Cambiar modo de autenticación

En el panel, ir a **Configuración del Servidor** y cambiar:
- **Modo de autenticación**: `database` o `both`
  - `database`: Solo usuarios con contraseña
  - `both`: Whitelist O usuarios con contraseña (cualquiera funciona)
  - `whitelist`: Solo whitelist (modo actual)
  - `public`: Sin autenticación

### Paso 2: Obtener API Key

El servidor tiene una API key única que se genera automáticamente. Se puede ver en:
- **Configuración del Servidor** → **API Key**

Esta key se usa en el plugin para autenticar las peticiones al panel.

### Paso 3: Instalar Plugin/Mod

Ver sección "Implementación del Plugin" más abajo.

## 👥 Gestión de Usuarios desde el Panel

### Crear Usuario

1. Ir a **Configuración del Servidor** → **Usuarios**
2. Click en **Crear Usuario**
3. Ingresar:
   - **Username**: Nombre del jugador (máx 16 caracteres)
   - **Password**: Contraseña inicial
   - **Email** (opcional): Para envío de tokens de recuperación

### Establecer Contraseña

Si el usuario no tiene contraseña establecida:
1. El sistema genera un token
2. Se envía por email (si está configurado)
3. El usuario puede establecer su contraseña usando el token

### Activar/Desactivar Usuario

- **Activo**: Puede conectarse al servidor
- **Inactivo**: No puede conectarse (pero se mantiene en la BD)

## 🔌 Implementación del Plugin

### Opción 1: Plugin Fabric (Recomendado para Cobblemon)

El servidor usa Fabric, por lo que necesitamos un mod de Fabric.

**Estructura básica del mod**:

```java
// Ejemplo simplificado - necesitaría implementación completa
public class PanelAuthMod implements ModInitializer {
    private static final String PANEL_URL = "http://panel-url/api/servers/{server_id}/auth/";
    private static final String API_KEY = "api_key_del_servidor";
    
    @Override
    public void onInitialize() {
        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {
            // Interceptar cuando un jugador se conecta
            String username = handler.getPlayer().getName().getString();
            
            // Solicitar contraseña (implementar sistema de chat/UI)
            // Validar contra panel
            // Permitir o rechazar conexión
        });
    }
}
```

### Opción 2: Plugin Bukkit/Spigot (Para servidores Paper)

Si el servidor usa Paper/Spigot, se puede usar un plugin Java estándar.

### Opción 3: Solución Temporal - Comando RCON

Mientras se implementa el plugin, se puede usar un sistema de comandos:

1. Jugador se conecta (pasa whitelist)
2. Jugador ejecuta: `/login usuario password`
3. El servidor valida contra el panel vía RCON script
4. Si es válido, se le da permisos; si no, se expulsa

## 🔐 Seguridad

- ✅ Contraseñas hasheadas con SHA256 + salt único
- ✅ API Key para proteger endpoints
- ✅ Validación de permisos en el panel
- ✅ Logs de autenticación
- ⚠️ **Importante**: Usar HTTPS para las peticiones del plugin al panel

## 📊 Endpoints Disponibles

### Autenticación
- `POST /api/servers/{server_id}/auth/` - Validar credenciales (usado por plugin)

### Gestión de Usuarios
- `GET /api/servers/{server_id}/users/` - Listar usuarios
- `POST /api/servers/{server_id}/users/create/` - Crear usuario
- `POST /api/servers/{server_id}/users/{user_id}/update/` - Actualizar usuario
- `POST /api/servers/{server_id}/users/{user_id}/delete/` - Eliminar usuario
- `POST /api/servers/{server_id}/users/set-password/` - Establecer contraseña

## 🎯 Próximos Pasos

1. **Implementar plugin/mod de Fabric** para interceptar conexiones
2. **Crear interfaz de login** en el juego (chat o GUI)
3. **Configurar servidor** para usar modo `database` o `both`
4. **Migrar usuarios** de whitelist a base de datos (opcional)

## 💡 Ventajas del Sistema

- ✅ **Gestión centralizada**: Todos los usuarios en el panel
- ✅ **Sin problemas de UUID**: No depende de whitelist.json
- ✅ **Recuperación de contraseña**: Sistema de tokens por email
- ✅ **Control granular**: Activar/desactivar usuarios sin eliminar
- ✅ **Auditoría**: Logs de autenticación y acceso
- ✅ **Flexibilidad**: Puede combinarse con whitelist (`both` mode)
