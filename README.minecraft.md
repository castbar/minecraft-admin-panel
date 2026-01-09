# Configuración de Servidor Minecraft

Este proyecto incluye un archivo `docker-compose.minecraft.yml` para crear servidores Minecraft de prueba que se pueden gestionar desde el panel de administración.

## Inicio Rápido

### 1. Crear el servidor con la versión por defecto (1.21.1)

```bash
docker-compose -f docker-compose.minecraft.yml up -d
```

### 2. Crear el servidor con una versión específica

```bash
MC_VERSION=1.20.1 docker-compose -f docker-compose.minecraft.yml up -d
```

### 3. Configuración personalizada completa

Puedes crear un archivo `.env.minecraft.local` con tus configuraciones:

```bash
# Copia el archivo de ejemplo
cp .env.minecraft .env.minecraft.local

# Edita el archivo con tus valores
nano .env.minecraft.local
```

Luego ejecuta:

```bash
docker-compose -f docker-compose.minecraft.yml --env-file .env.minecraft.local up -d
```

## Variables de Entorno Disponibles

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `CONTAINER_NAME` | Nombre del contenedor Docker | `minecraft-server-1` |
| `GAME_PORT` | Puerto del juego Minecraft | `25565` |
| `RCON_PORT` | Puerto RCON para control remoto | `25575` |
| `SERVER_TYPE` | Tipo de servidor (VANILLA, FORGE, FABRIC, etc.) | `VANILLA` |
| `MC_VERSION` | Versión de Minecraft | `1.21.1` |
| `MEMORY` | Memoria RAM asignada | `2G` |
| `RCON_PASSWORD` | Contraseña RCON | `password123` |
| `DIFFICULTY` | Dificultad (peaceful, easy, normal, hard) | `normal` |
| `MAX_PLAYERS` | Máximo de jugadores | `20` |
| `ONLINE_MODE` | Verificación de cuentas Mojang | `false` |
| `PVP` | Habilitar PvP | `true` |
| `WHITELIST` | Habilitar whitelist | `false` |
| `MOTD` | Mensaje del día | `Servidor de Prueba - Minecraft Admin Panel` |
| `SERVER_NAME` | Nombre del servidor | `Servidor de Prueba` |

## Ejemplos de Uso

### Servidor Vanilla 1.21.1 (por defecto)
```bash
docker-compose -f docker-compose.minecraft.yml up -d
```

### Servidor Vanilla 1.20.1
```bash
MC_VERSION=1.20.1 docker-compose -f docker-compose.minecraft.yml up -d
```

### Servidor Forge 1.20.1
```bash
SERVER_TYPE=FORGE MC_VERSION=1.20.1 docker-compose -f docker-compose.minecraft.yml up -d
```

### Servidor con más memoria
```bash
MEMORY=4G docker-compose -f docker-compose.minecraft.yml up -d
```

### Servidor en modo online con whitelist
```bash
ONLINE_MODE=true WHITELIST=true docker-compose -f docker-compose.minecraft.yml up -d
```

## Agregar el Servidor al Panel

Una vez que el servidor esté corriendo, ve al panel web en `http://localhost:8080` y:

1. Inicia sesión (usuario: `admin`, contraseña: `admin123`)
2. Haz clic en "Crear Servidor"
3. Completa el formulario:
   - **Nombre**: Servidor de Prueba
   - **Host**: minecraft-server-1
   - **Puerto**: 25565
   - **Puerto RCON**: 25575
   - **Contraseña RCON**: password123 (o la que configuraste)
   - **Tipo**: vanilla
   - **Versión**: 1.21.1 (o la que configuraste)

4. Haz clic en "Crear Servidor"

## Gestión del Servidor

### Ver logs
```bash
docker logs -f minecraft-server-1
```

### Detener el servidor
```bash
docker-compose -f docker-compose.minecraft.yml down
```

### Reiniciar el servidor
```bash
docker-compose -f docker-compose.minecraft.yml restart
```

### Eliminar el servidor y sus datos
```bash
docker-compose -f docker-compose.minecraft.yml down -v
```

## Versiones de Minecraft Soportadas

El contenedor `itzg/minecraft-server` soporta muchas versiones. Algunas populares:

- **1.21.1** (última estable)
- **1.20.1** (muy popular para mods)
- **1.19.4**
- **1.18.2**
- **1.16.5** (muy popular para mods)
- **1.12.2** (muy popular para mods antiguos)
- **LATEST** (última versión disponible)

Para más información sobre versiones y tipos de servidores, visita:
https://github.com/itzg/docker-minecraft-server

## Solución de Problemas

### El servidor no aparece en el panel
- Verifica que el contenedor esté corriendo: `docker ps | grep minecraft`
- Verifica que esté en la red correcta: `docker network inspect minecraft-servers`
- Verifica los logs: `docker logs minecraft-server-1`

### No puedo conectarme al servidor
- Verifica que el puerto esté abierto: `netstat -an | grep 25565`
- Verifica que el servidor esté corriendo: `docker ps`
- Intenta conectarte desde el panel usando RCON

### El servidor se queda sin memoria
- Aumenta la memoria: `MEMORY=4G docker-compose -f docker-compose.minecraft.yml up -d`
- Verifica el uso de recursos: `docker stats minecraft-server-1`

