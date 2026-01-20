# Instrucciones para Ejecutar Migración de Ownership

## 📋 Pasos a Seguir

### 1. Agregar Variable de Encriptación al .env

Agregar al archivo `.env` (en el directorio raíz del proyecto):

```bash
ENCRYPTION_KEY=hpCdFZ_jJODR1y6OX_gFjjfp19ygl_nY3nWJYAwCk9E=
```

**⚠️ IMPORTANTE:** Esta clave es única y debe guardarse de forma segura. Si se pierde, no se podrán desencriptar las contraseñas RCON existentes.

### 2. Ejecutar Migración

Conectarse al contenedor y ejecutar la migración:

```bash
# Conectarse al contenedor
docker exec -it minecraft-admin-panel bash

# Ejecutar migración
python manage.py migrate

# Salir del contenedor
exit
```

### 3. Verificar Migración

Verificar que los servidores existentes tengan owner asignado:

```bash
# Conectarse al contenedor
docker exec -it minecraft-admin-panel bash

# Abrir shell de Django
python manage.py shell

# Verificar servidores
from server.models import Server
from django.contrib.auth.models import User

# Ver todos los servidores y sus owners
for server in Server.objects.all():
    print(f"Servidor: {server.name}, Owner: {server.owner.username if server.owner else 'SIN OWNER'}")

# Si algún servidor no tiene owner, asignarlo manualmente:
admin = User.objects.filter(is_superuser=True).first()
if admin:
    Server.objects.filter(owner__isnull=True).update(owner=admin)
    print(f"✅ Servidores sin owner asignados a: {admin.username}")

exit()
```

### 4. Reiniciar Contenedor (si es necesario)

```bash
docker compose restart minecraft-admin-panel
```

## ✅ Verificación Post-Migración

1. **Crear un usuario nuevo:**
   - Login como staff
   - Ir a "Gestión de Usuarios"
   - Crear un nuevo usuario (is_staff=false)
   - Verificar que se crea correctamente

2. **Crear un servidor nuevo:**
   - Login como el usuario nuevo
   - Crear un servidor
   - Verificar que el servidor tiene `owner = usuario_nuevo`
   - Verificar que solo ese usuario puede ver su servidor

3. **Verificar encriptación:**
   - Crear un servidor con contraseña RCON
   - Verificar en la BD que la contraseña está encriptada
   - Verificar que la conexión RCON funciona (se desencripta automáticamente)

## 🔐 Seguridad

- **ENCRYPTION_KEY:**** Debe estar en `.env` y NO subirse a Git
- **Contraseñas RCON:** Se encriptan automáticamente al guardar
- **Desencriptación:** Se hace automáticamente al usar `server.get_rcon_password()`

## 🚨 Troubleshooting

### Si la migración falla:

```bash
# Ver logs del contenedor
docker logs minecraft-admin-panel

# Verificar estado de migraciones
docker exec -it minecraft-admin-panel python manage.py showmigrations server
```

### Si algún servidor no tiene owner:

```python
# En Django shell
from server.models import Server
from django.contrib.auth.models import User

admin = User.objects.filter(is_superuser=True).first()
Server.objects.filter(owner__isnull=True).update(owner=admin)
```

### Si las contraseñas RCON no funcionan:

1. Verificar que `ENCRYPTION_KEY` está en `.env`
2. Reiniciar el contenedor
3. Verificar logs: `docker logs minecraft-admin-panel`
