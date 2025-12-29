#!/bin/bash
# Test del flujo de registro por email ejecutado dentro del contenedor

set -e

echo "============================================================"
echo "TEST: Flujo de Registro por Email (Servidor Real)"
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
print('TEST: Flujo de Registro por Email')
print('=' * 60)

client = Client()

# Obtener o crear usuario admin
admin_user, created = User.objects.get_or_create(
    username='test_admin_email',
    defaults={'is_staff': True, 'is_superuser': True}
)
admin_user.set_password('test_password_123')
admin_user.save()

# Buscar o crear servidor con auth_mode='database'
test_server = Server.objects.filter(auth_mode='database', is_active=True).first()
if not test_server:
    # Crear servidor de prueba
    test_server = Server.objects.create(
        name='Test Server Email',
        host='test-server-email.local',
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
        'username': 'test_admin_email',
        'password': 'test_password_123'
    }),
    content_type='application/json'
)

if login_response.status_code != 200:
    print(f'❌ Error de autenticación: {login_response.status_code}')
    sys.exit(1)

print('✅ Autenticación exitosa')

# 1. Admin crea usuario (sin contraseña)
print('\n' + '=' * 60)
print('🧪 TEST 1: Admin crea usuario (sin contraseña)')
print('=' * 60)

test_username = f'testuser_{int(time.time())}'
test_email = f'test_{int(time.time())}@example.com'

print(f'   Creando usuario: {test_username}')
print(f'   Email: {test_email}')

create_response = client.post(
    f'/api/servers/{server_id}/users/create/',
    json.dumps({
        'username': test_username,
        'email': test_email
    }),
    content_type='application/json'
)

print(f'   Status Code: {create_response.status_code}')

if create_response.status_code != 200:
    print(f'   ❌ Error: {create_response.status_code}')
    print(create_response.content.decode()[:200])
    sys.exit(1)

create_data = json.loads(create_response.content)
if not create_data.get('success'):
    print(f'   ❌ Error: {create_data.get(\"error\")}')
    sys.exit(1)

print(f'   ✅ Usuario creado exitosamente!')
print(f'   Mensaje: {create_data.get(\"message\")}')

user_data = create_data.get('data', {})
user_id = user_data.get('id')
print(f'   - ID: {user_id}')
print(f'   - is_active: {user_data.get(\"is_active\")} (debe ser False)')
print(f'   - has_password_set: {user_data.get(\"has_password_set\")} (debe ser False)')

# Verificar en BD
user_obj = MinecraftUser.objects.get(id=user_id, server=test_server)
print(f'   ✅ Usuario verificado en BD')
print(f'   - Email: {user_obj.email}')
print(f'   - Token generado: {bool(user_obj.password_set_token)}')
print(f'   - Token expira: {user_obj.password_set_token_expires}')

if not user_obj.password_set_token:
    print(f'   ❌ Error: No se generó token')
    sys.exit(1)

token = user_obj.password_set_token
print(f'   ✅ Token obtenido: {token[:20]}...')

# 2. Usuario establece contraseña con token
print('\n' + '=' * 60)
print('🧪 TEST 2: Usuario establece contraseña con token')
print('=' * 60)

test_password = 'mypassword123'
print(f'   Estableciendo contraseña para usuario: {test_username}')
print(f'   Token: {token[:20]}...')

set_password_response = client.post(
    f'/api/servers/{server_id}/users/set-password/',
    json.dumps({
        'token': token,
        'password': test_password
    }),
    content_type='application/json'
)

print(f'   Status Code: {set_password_response.status_code}')

if set_password_response.status_code != 200:
    print(f'   ❌ Error: {set_password_response.status_code}')
    print(set_password_response.content.decode()[:200])
    sys.exit(1)

set_password_data = json.loads(set_password_response.content)
if not set_password_data.get('success'):
    print(f'   ❌ Error: {set_password_data.get(\"error\")}')
    sys.exit(1)

print(f'   ✅ Contraseña establecida exitosamente!')
print(f'   Mensaje: {set_password_data.get(\"message\")}')

# Verificar en BD
user_obj.refresh_from_db()
print(f'   ✅ Usuario actualizado en BD')
print(f'   - is_active: {user_obj.is_active} (debe ser True)')
print(f'   - has_password_set: {user_obj.has_password_set()} (debe ser True)')
print(f'   - Token limpiado: {not user_obj.password_set_token} (debe ser True)')

if not user_obj.is_active:
    print(f'   ❌ Error: Usuario no está activo')
    sys.exit(1)

if not user_obj.has_password_set():
    print(f'   ❌ Error: Contraseña no se estableció')
    sys.exit(1)

# 3. Verificar que la contraseña funciona
print('\n' + '=' * 60)
print('🧪 TEST 3: Verificar autenticación con contraseña')
print('=' * 60)

if user_obj.check_password(test_password):
    print(f'   ✅ Contraseña verificada correctamente')
else:
    print(f'   ❌ Error: La contraseña no se verificó')
    sys.exit(1)

# 4. Probar autenticación completa
authenticated_user = MinecraftUser.authenticate(test_server, test_username, test_password)
if authenticated_user:
    print(f'   ✅ Autenticación completa exitosa')
    print(f'   - Usuario: {authenticated_user.username}')
    print(f'   - last_login: {authenticated_user.last_login}')
else:
    print(f'   ❌ Error: Autenticación falló')
    sys.exit(1)

# 5. Limpiar - eliminar usuario de prueba
print('\n' + '=' * 60)
print('🧹 Limpiando usuario de prueba')
print('=' * 60)

user_obj.delete()
print(f'   ✅ Usuario {test_username} eliminado')

print('\n' + '=' * 60)
print('📊 RESUMEN')
print('=' * 60)
print('✅ Flujo completo de registro por email testeado exitosamente')
print('✅ Admin crea usuario sin contraseña')
print('✅ Token generado y email preparado (console backend)')
print('✅ Usuario establece contraseña con token')
print('✅ Usuario puede autenticarse correctamente')
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

