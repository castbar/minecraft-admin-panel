#!/bin/bash
# Test de endpoints de usuarios de Minecraft ejecutado dentro del contenedor

set -e

echo "============================================================"
echo "TEST: Endpoints de Usuarios de Minecraft"
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
print('TEST: Endpoints de Usuarios de Minecraft')
print('=' * 60)

client = Client()

# Obtener o crear usuario admin
admin_user, created = User.objects.get_or_create(
    username='test_admin_users',
    defaults={'is_staff': True, 'is_superuser': True}
)
admin_user.set_password('test_password_123')
admin_user.save()

# Buscar servidor cobblemon
cobblemon_server = Server.objects.filter(container_name='cobblemon-server').first()
if not cobblemon_server:
    cobblemon_server = Server.objects.filter(name__icontains='cobblemon').first()

if cobblemon_server:
    server_id = cobblemon_server.id
    server_name = cobblemon_server.name
    auth_mode = cobblemon_server.auth_mode
    # Asegurar que el usuario tenga acceso
    UserServerRole.objects.get_or_create(
        user=admin_user,
        server=cobblemon_server,
        defaults={'role': 'admin'}
    )
    print(f'✅ Servidor encontrado: {server_name} (ID: {server_id})')
    print(f'   auth_mode: {auth_mode}')
else:
    print('❌ No se encontró servidor cobblemon')
    sys.exit(1)

# Login con JSON
import json as json_lib
login_response = client.post(
    '/api/auth/login/',
    json_lib.dumps({
        'username': 'test_admin_users',
        'password': 'test_password_123'
    }),
    content_type='application/json'
)

if login_response.status_code != 200:
    print(f'❌ Error de autenticación: {login_response.status_code}')
    sys.exit(1)

print('✅ Autenticación exitosa')

# 1. Test GET /api/servers/<id>/users/
print('\n' + '=' * 60)
print('🧪 TEST 1: GET /api/servers/<id>/users/')
print('=' * 60)

users_list_response = client.get(f'/api/servers/{server_id}/users/')
print(f'   Status Code: {users_list_response.status_code}')

if users_list_response.status_code == 400:
    error_data = json.loads(users_list_response.content)
    if 'database authentication' in error_data.get('error', '').lower():
        print(f'   ✅ Comportamiento esperado: Servidor no usa autenticación por BD')
        print(f'   Error: {error_data.get(\"error\")}')
    else:
        print(f'   ⚠️  Error inesperado: {error_data.get(\"error\")}')
elif users_list_response.status_code == 200:
    users_data = json.loads(users_list_response.content)
    if users_data.get('success'):
        users = users_data.get('data', [])
        print(f'   ✅ Usuarios encontrados: {len(users)}')
        for user in users[:5]:
            print(f'      - {user.get(\"username\")} (activo: {user.get(\"is_active\")})')
    else:
        print(f'   ❌ Error: {users_data.get(\"error\")}')
else:
    print(f'   ❌ Error inesperado: {users_list_response.status_code}')

# 2. Test POST /api/servers/<id>/users/create/
print('\n' + '=' * 60)
print('🧪 TEST 2: POST /api/servers/<id>/users/create/')
print('=' * 60)

test_username = f'testuser_{int(time.time())}'
test_password = 'testpass123'

print(f'   Intentando crear usuario: {test_username}')

create_response = client.post(
    f'/api/servers/{server_id}/users/create/',
    json.dumps({
        'username': test_username,
        'password': test_password
    }),
    content_type='application/json'
)

print(f'   Status Code: {create_response.status_code}')

if create_response.status_code == 400:
    error_data = json.loads(create_response.content)
    if 'database authentication' in error_data.get('error', '').lower():
        print(f'   ✅ Comportamiento esperado: Servidor no usa autenticación por BD')
        print(f'   Error: {error_data.get(\"error\")}')
    else:
        print(f'   ⚠️  Error de validación: {error_data.get(\"error\")}')
elif create_response.status_code == 403:
    print(f'   ❌ Error 403 - CSRF o permisos')
    print(create_response.content.decode()[:200])
elif create_response.status_code == 200:
    create_data = json.loads(create_response.content)
    if create_data.get('success'):
        print(f'   ✅ Usuario creado exitosamente!')
        user_data = create_data.get('data', {})
        print(f'   ID: {user_data.get(\"id\")}')
        print(f'   Username: {user_data.get(\"username\")}')
        
        # Verificar que el usuario existe en la BD
        user_obj = MinecraftUser.objects.filter(server=cobblemon_server, username=test_username).first()
        if user_obj:
            print(f'   ✅ Usuario verificado en BD')
            print(f'   - Password hash existe: {bool(user_obj.password_hash)}')
            print(f'   - Salt existe: {bool(user_obj.salt)}')
            
            # Verificar que la contraseña funciona
            if user_obj.check_password(test_password):
                print(f'   ✅ Contraseña verificada correctamente')
            else:
                print(f'   ❌ Error: La contraseña no se verificó correctamente')
            
            test_user_id = user_obj.id
        else:
            print(f'   ❌ Error: Usuario no encontrado en BD')
    else:
        print(f'   ❌ Error: {create_data.get(\"error\")}')
else:
    print(f'   ❌ Error inesperado: {create_response.status_code}')
    print(create_response.content.decode()[:200])

# 3. Test POST /api/servers/<id>/users/<user_id>/update/ (solo si se creó el usuario)
if create_response.status_code == 200 and 'test_user_id' in locals():
    print('\n' + '=' * 60)
    print('🧪 TEST 3: POST /api/servers/<id>/users/<user_id>/update/')
    print('=' * 60)
    
    new_password = 'newpass456'
    print(f'   Actualizando contraseña del usuario {test_username}')
    
    update_response = client.post(
        f'/api/servers/{server_id}/users/{test_user_id}/update/',
        json.dumps({
            'password': new_password
        }),
        content_type='application/json'
    )
    
    print(f'   Status Code: {update_response.status_code}')
    
    if update_response.status_code == 200:
        update_data = json.loads(update_response.content)
        if update_data.get('success'):
            print(f'   ✅ Usuario actualizado exitosamente!')
            
            # Verificar que la nueva contraseña funciona
            user_obj.refresh_from_db()
            if user_obj.check_password(new_password):
                print(f'   ✅ Nueva contraseña verificada correctamente')
            else:
                print(f'   ❌ Error: La nueva contraseña no se verificó')
    else:
        print(f'   ⚠️  Error: {update_response.status_code}')
        print(update_response.content.decode()[:200])
    
    # 4. Test DELETE /api/servers/<id>/users/<user_id>/delete/
    print('\n' + '=' * 60)
    print('🧪 TEST 4: DELETE /api/servers/<id>/users/<user_id>/delete/')
    print('=' * 60)
    
    print(f'   Eliminando usuario {test_username}')
    
    delete_response = client.delete(f'/api/servers/{server_id}/users/{test_user_id}/delete/')
    
    print(f'   Status Code: {delete_response.status_code}')
    
    if delete_response.status_code == 200:
        delete_data = json.loads(delete_response.content)
        if delete_data.get('success'):
            print(f'   ✅ Usuario eliminado exitosamente!')
            
            # Verificar que el usuario ya no existe
            user_obj = MinecraftUser.objects.filter(server=cobblemon_server, username=test_username).first()
            if not user_obj:
                print(f'   ✅ Usuario verificado como eliminado en BD')
            else:
                print(f'   ❌ Error: Usuario aún existe en BD')
    else:
        print(f'   ⚠️  Error: {delete_response.status_code}')
        print(delete_response.content.decode()[:200])

print('\n' + '=' * 60)
print('📊 RESUMEN')
print('=' * 60)
print('✅ Endpoints de usuarios de Minecraft revisados')
if auth_mode not in ['database', 'both']:
    print(f'ℹ️  Servidor usa auth_mode=\"{auth_mode}\", por lo que estos endpoints retornan 400 (comportamiento esperado)')
    print('ℹ️  Para probar completamente, cambiar auth_mode a \"database\" o \"both\"')
print('=' * 60)
"
EOF

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ Test completado"
else
    echo ""
    echo "❌ Test falló con código: $EXIT_CODE"
fi

exit $EXIT_CODE

