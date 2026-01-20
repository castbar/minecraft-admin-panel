# Comandos para Ejecutar Migración

## ✅ Variable ENCRYPTION_KEY agregada al .env

La variable `ENCRYPTION_KEY` ya fue agregada al archivo `.env`.

## 🔄 Ejecutar Migración

Cuando el contenedor `minecraft-admin-panel` esté corriendo, ejecutar:

```bash
# Opción 1: Ejecutar migración directamente
docker exec -it minecraft-admin-panel python manage.py migrate

# Opción 2: Si necesitas reiniciar el contenedor primero (para cargar la nueva variable)
docker compose restart minecraft-admin-panel
docker exec -it minecraft-admin-panel python manage.py migrate
```

## ✅ Verificar Migración

Después de ejecutar la migración, verificar que todo esté correcto:

```bash
# Conectarse al contenedor
docker exec -it minecraft-admin-panel bash

# Abrir shell de Django
python manage.py shell

# Verificar servidores y owners
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

## 🔐 Verificar Encriptación

Verificar que la encriptación funciona:

```python
# En Django shell
from server.models import Server
from server.utils.encryption import is_encrypted

# Verificar que las contraseñas RCON están encriptadas
for server in Server.objects.all():
    encrypted = is_encrypted(server.rcon_password)
    print(f"Servidor: {server.name}, Contraseña encriptada: {encrypted}")
    
    # Probar desencriptación
    password = server.get_rcon_password()
    print(f"  Contraseña desencriptada: {'*' * len(password) if password else 'None'}")
```

## 📝 Notas

- La migración asignará automáticamente los servidores existentes al primer superuser
- Las contraseñas RCON existentes se encriptarán automáticamente la próxima vez que se guarden
- La variable `ENCRYPTION_KEY` debe estar en el `.env` para que funcione la encriptación
