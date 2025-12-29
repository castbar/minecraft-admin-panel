# Explicación: Sistema Multi-Servidor

## ¿Qué es "servidor activo"?

**IMPORTANTE**: "Servidor activo" NO significa que solo un servidor esté ejecutándose. Significa **qué servidor está seleccionado actualmente en el panel web/frontend** para el usuario.

## Cómo funciona

### 1. Múltiples servidores ejecutándose simultáneamente

✅ **SÍ, puedes tener múltiples servidores ejecutándose al mismo tiempo**
- Cada servidor es un contenedor Docker independiente
- Cada servidor tiene su propia configuración
- Cada servidor puede tener su propio puerto de juego

### 2. Puertos de Minecraft

Cada servidor Minecraft puede usar un puerto diferente:

**Puerto del juego (para jugadores):**
- Por defecto: `25565`
- Configurable en `server.properties` de cada servidor: `server-port=25565`
- Los jugadores se conectan usando: `IP:PUERTO` o `DNS:PUERTO`

**Puerto RCON (para administración):**
- Configurado en el modelo `Server`: campo `rcon_port` (por defecto `25575`)
- Cada servidor puede tener su propio puerto RCON

### 3. Endpoint `switch_server`

Este endpoint **NO afecta qué servidor está ejecutándose**. Solo cambia:

- **Qué servidor está "seleccionado" en el panel web** para el usuario
- Guarda una sesión (`ServerSession`) para recordar el último servidor usado
- Permite que el frontend muestre datos del servidor correcto

**Ejemplo:**
```
Usuario tiene acceso a 3 servidores:
- Servidor A (cobblemon) - Puerto 25565
- Servidor B (survival) - Puerto 25566  
- Servidor C (creative) - Puerto 25567

Todos pueden estar ejecutándose al mismo tiempo.
El usuario puede "cambiar" entre ellos en el panel para ver/administrar cada uno.
```

### 4. Conexión de jugadores

Los jugadores se conectan directamente a cada servidor usando:

```
Servidor Cobblemon:   192.168.0.236:25565
Servidor Survival:    192.168.0.236:25566
Servidor Creative:    192.168.0.236:25567
```

O usando DNS:
```
cobblemon.castbar.dev:25565
survival.castbar.dev:25566
creative.castbar.dev:25567
```

### 5. Modelo Server

```python
class Server:
    host = "DNS o IP del servidor"
    rcon_port = 25575  # Puerto RCON (administración)
    minecraft_data_path = "/data"  # Ruta de datos
    # NO hay campo para puerto del juego (se configura en server.properties)
```

**Nota**: El puerto del juego se configura en `server.properties` de cada servidor, no en el modelo Django.

## Flujo típico

1. **Admin crea múltiples servidores** en el panel
   - Cada uno con su `host`, `rcon_port`, `minecraft_data_path`
   - Cada uno puede tener su propio `server.properties` con `server-port` diferente

2. **Todos los servidores pueden ejecutarse simultáneamente**
   - Cada uno en su propio contenedor Docker
   - Cada uno escuchando en su puerto

3. **Usuario del panel "cambia" entre servidores**
   - `POST /api/servers/switch/` cambia qué servidor está "activo" en el panel
   - Esto solo afecta qué datos se muestran en el frontend
   - NO afecta qué servidores están ejecutándose

4. **Jugadores se conectan directamente**
   - Cada jugador elige a qué servidor conectarse usando IP:PUERTO
   - No hay un "servidor activo" desde la perspectiva del jugador

## Resumen

- ✅ **Múltiples servidores pueden ejecutarse simultáneamente**
- ✅ **Cada servidor puede tener su propio puerto** (configurado en `server.properties`)
- ✅ **`switch_server` solo cambia qué servidor está seleccionado en el panel web**
- ✅ **Los jugadores se conectan directamente usando IP:PUERTO de cada servidor**

El sistema está diseñado para **multi-servidor real**, no para alternar entre servidores.

