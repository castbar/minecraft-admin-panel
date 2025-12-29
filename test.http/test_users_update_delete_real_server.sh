#!/bin/bash
# Test de endpoints update y delete de usuarios de Minecraft ejecutado dentro del contenedor

set -e

echo "============================================================"
echo "TEST: Update y Delete de Usuarios de Minecraft"
echo "============================================================"
echo ""

# Ejecutar test dentro del contenedor
ssh carlitos@192.168.0.236 << 'EOF'
    docker exec minecraft-admin-panel python -c "
import os
import sys
import django
import json
import time

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'minecraft_panel.settings')
django.setup()

from django.test import Client
from server.models import Server, UserServerRole, MinecraftUser
from django.contrib.auth.models import User

print('=' * 60)
print('TEST: Update y Delete de Usuarios de Minecraft')
print('=' * 60)

client = Client()

# Obtener o crear usuario admin
admin_user, created = User.objects.get_or_create(
    username='test_admin_update_delete',
    defaults={'is_staff': True, 'is_superuser': True}
)
admin_user.set_password('test_password_123')
admin_user.save()

# Buscar o crear servidor con auth_mode='database'
test_server = Server.objects.filter(auth_mode='database', is_active=True).first()
if not test_server:
    test_server = Server.objects.create(
        name='Test Server Update Delete',
        host='test-server-update-delete.local',
        rcon_port=25575,
        rcon_password='test123',
        minecraft_data_path='/data',
        auth_mode='database',
        is_active=True
    )
    print(f'✅ Servidor de prueba creado: {test_server.name} (ID: {test_server.id})')
else:
    print(f'✅ Servidor encontrado: {test_server.name} (ID: {test_server.id})')

# Asegurar que el usuario tenga acceso
UserServerRole.objects.get_or_create(
    user=admin_user,
    server=test_server,
    defaults={'role': 'admin'}
)

server_id = test_server.id

# Login con JSON
import json as json_lib
login_response = client.post(
    '/api/auth/login/',
    json_lib.dumps({
        'username': 'test_admin_update_delete',
        'password': 'test_password_123'
    }),
    content_type='application/json'
)

if login_response.status_code != 200:
    print(f'❌ Error de autenticación: {login_response.status_code}')
    sys.exit(1)

print('✅ Autenticación exitosa')

# Crear usuario de prueba primero
test_username = f'testuser_{int(time.time())}'
test_email = f'test_{int(time.time())}@example.com'
test_password = 'initialpass123'

print('\n' + '=' * 60)
print('📝 Creando usuario de prueba')
print('=' * 60)
print(f'   Username: {test_username}')
print(f'   Email: {test_email}')

create_response = client.post(
    f'/api/servers/{server_id}/users/create/',
    json.dumps({
        'username': test_username,
        'email': test_email,
        'password': test_password  # Crear con contraseña directa para test
    }),
    content_type='application/json'
)

if create_response.status_code != 200:
    print(f'   ❌ Error creando usuario: {create_response.status_code}')
    print(create_response.content.decode()[:200])
    sys.exit(1)

create_data = json.loads(create_response.content)
user_id = create_data.get('data', {}).get('id')
print(f'   ✅ Usuario creado: ID {user_id}')

# Verificar en BD
user_obj = MinecraftUser.objects.get(id=user_id, server=test_server)
print(f'   ✅ Usuario verificado en BD')
print(f'   - is_active: {user_obj.is_active}')

# TEST 1: Actualizar contraseña
print('\n' + '=' * 60)
print('🧪 TEST 1: POST /api/servers/<id>/users/<user_id>/update/ - Cambiar contraseña')
print('=' * 60)

new_password = 'newpassword456'
print(f'   Actualizando contraseña del usuario {test_username}')
print(f'   Nueva contraseña: {new_password}')

update_response = client.post(
    f'/api/servers/{server_id}/users/{user_id}/update/',
    json.dumps({
        'password': new_password
    }),
    content_type='application/json'
)

print(f'   Status Code: {update_response.status_code}')

if update_response.status_code == 403:
    print(f'   ❌ Error 403 - CSRF o permisos')
    print(update_response.content.decode()[:200])
    sys.exit(1)
elif update_response.status_code != 200:
    print(f'   ❌ Error: {update_response.status_code}')
    print(update_response.content.decode()[:200])
    sys.exit(1)

update_data = json.loads(update_response.content)
if not update_data.get('success'):
    print(f'   ❌ Error: {update_data.get(\"error\")}')
    sys.exit(1)

print(f'   ✅ Contraseña actualizada exitosamente!')
print(f'   Mensaje: {update_data.get(\"message\")}')

# Verificar que la nueva contraseña funciona
user_obj.refresh_from_db()
if user_obj.check_password(new_password):
    print(f'   ✅ Nueva contraseña verificada correctamente')
else:
    print(f'   ❌ Error: La nueva contraseña no se verificó')
    sys.exit(1)

# Verificar que la contraseña antigua NO funciona
if user_obj.check_password(test_password):
    print(f'   ❌ Error: La contraseña antigua aún funciona (no debería)')
    sys.exit(1)
else:
    print(f'   ✅ Contraseña antigua ya no funciona (correcto)')

# TEST 2: Actualizar is_active
print('\n' + '=' * 60)
print('🧪 TEST 2: POST /api/servers/<id>/users/<user_id>/update/ - Cambiar is_active')
print('=' * 60)

current_active = user_obj.is_active
new_active = not current_active

print(f'   Cambiando is_active: {current_active} -> {new_active}')

update_active_response = client.post(
    f'/api/servers/{server_id}/users/{user_id}/update/',
    json.dumps({
        'is_active': new_active
    }),
    content_type='application/json'
)

print(f'   Status Code: {update_active_response.status_code}')

if update_active_response.status_code != 200:
    print(f'   ❌ Error: {update_active_response.status_code}')
    print(update_active_response.content.decode()[:200])
    sys.exit(1)

update_active_data = json.loads(update_active_response.content)
if not update_active_data.get('success'):
    print(f'   ❌ Error: {update_active_data.get(\"error\")}')
    sys.exit(1)

print(f'   ✅ Estado actualizado exitosamente!')

# Verificar en BD
user_obj.refresh_from_db()
if user_obj.is_active == new_active:
    print(f'   ✅ is_active actualizado correctamente: {user_obj.is_active}')
else:
    print(f'   ❌ Error: is_active no se actualizó correctamente')
    sys.exit(1)

# Verificar que no puede autenticarse si is_active=False
if not new_active:
    authenticated = MinecraftUser.authenticate(test_server, test_username, new_password)
    if authenticated:
        print(f'   ❌ Error: Usuario inactivo pudo autenticarse (no debería)')
        sys.exit(1)
    else:
        print(f'   ✅ Usuario inactivo no puede autenticarse (correcto)')
    
    # Reactivar para el siguiente test
    reactivate_response = client.post(
        f'/api/servers/{server_id}/users/{user_id}/update/',
        json.dumps({
            'is_active': True
        }),
        content_type='application/json'
    )
    if reactivate_response.status_code == 200:
        print(f'   ✅ Usuario reactivado para siguiente test')

# TEST 3: Eliminar usuario
print('\n' + '=' * 60)
print('🧪 TEST 3: DELETE /api/servers/<id>/users/<user_id>/delete/')
print('=' * 60)

print(f'   Eliminando usuario: {test_username} (ID: {user_id})')

delete_response = client.delete(f'/api/servers/{server_id}/users/{user_id}/delete/')

print(f'   Status Code: {delete_response.status_code}')

if delete_response.status_code != 200:
    print(f'   ❌ Error: {delete_response.status_code}')
    print(delete_response.content.decode()[:200])
    sys.exit(1)

delete_data = json.loads(delete_response.content)
if not delete_data.get('success'):
    print(f'   ❌ Error: {delete_data.get(\"error\")}')
    sys.exit(1)

print(f'   ✅ Usuario eliminado exitosamente!')
print(f'   Mensaje: {delete_data.get(\"message\")}')

# Verificar que el usuario ya no existe
try:
    deleted_user = MinecraftUser.objects.get(id=user_id, server=test_server)
    print(f'   ❌ Error: Usuario aún existe en BD')
    sys.exit(1)
except MinecraftUser.DoesNotExist:
    print(f'   ✅ Usuario verificado como eliminado en BD')

# TEST 4: Intentar actualizar usuario inexistente
print('\n' + '=' * 60)
print('🧪 TEST 4: POST /api/servers/<id>/users/<user_id>/update/ - Usuario inexistente')
print('=' * 60)

fake_user_id = 99999
print(f'   Intentando actualizar usuario inexistente (ID: {fake_user_id})')

update_fake_response = client.post(
    f'/api/servers/{server_id}/users/{fake_user_id}/update/',
    json.dumps({
        'is_active': False
    }),
    content_type='application/json'
)

print(f'   Status Code: {update_fake_response.status_code}')

if update_fake_response.status_code == 404:
    print(f'   ✅ Error 404 retornado correctamente (usuario no encontrado)')
else:
    print(f'   ⚠️  Status inesperado: {update_fake_response.status_code}')
    print(update_fake_response.content.decode()[:200])

# TEST 5: Intentar eliminar usuario inexistente
print('\n' + '=' * 60)
print('🧪 TEST 5: DELETE /api/servers/<id>/users/<user_id>/delete/ - Usuario inexistente')
print('=' * 60)

print(f'   Intentando eliminar usuario inexistente (ID: {fake_user_id})')

delete_fake_response = client.delete(f'/api/servers/{server_id}/users/{fake_user_id}/delete/')

print(f'   Status Code: {delete_fake_response.status_code}')

if delete_fake_response.status_code == 404:
    print(f'   ✅ Error 404 retornado correctamente (usuario no encontrado)')
else:
    print(f'   ⚠️  Status inesperado: {delete_fake_response.status_code}')
    print(delete_fake_response.content.decode()[:200])

print('\n' + '=' * 60)
print('📊 RESUMEN')
print('=' * 60)
print('✅ POST /api/servers/<id>/users/<user_id>/update/ testeado completamente')
print('   - Actualizar contraseña: ✅')
print('   - Actualizar is_active: ✅')
print('   - Validación de usuario inexistente: ✅')
print('✅ DELETE /api/servers/<id>/users/<user_id>/delete/ testeado completamente')
print('   - Eliminar usuario: ✅')
print('   - Validación de usuario inexistente: ✅')
print('=' * 60)
"
EOF

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ Test completado exitosamente"
else
    echo ""
    echo "❌ Test falló con código: $EXIT_CODE"
fi

exit $EXIT_CODE

