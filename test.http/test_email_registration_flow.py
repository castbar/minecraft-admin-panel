#!/usr/bin/env python3
"""
Test del flujo completo de registro por email:
1. Admin crea usuario (sin contraseña)
2. Se genera token y se "envía" email (console backend)
3. Usuario establece contraseña con token
4. Usuario puede autenticarse
"""

import os
import sys
import django
import json

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'minecraft_panel.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from server.models.models import Server, UserServerRole, MinecraftUser
from django.utils import timezone

User = get_user_model()

def test_email_registration_flow():
    """Test del flujo completo de registro por email"""
    print("=" * 60)
    print("TEST: Flujo de Registro por Email")
    print("=" * 60)
    
    client = Client()
    
    # Login como admin
    username = os.environ.get('TEST_USER', 'admin')
    password = os.environ.get('TEST_PASSWORD', 'admin')
    
    login_response = client.post('/api/auth/login/', {
        'username': username,
        'password': password
    })
    
    if login_response.status_code != 200:
        print(f"❌ Error de autenticación: {login_response.status_code}")
        print(login_response.content.decode())
        return False
    
    print("✅ Autenticación exitosa")
    
    # Obtener servidor con auth_mode='database' o 'both'
    servers_response = client.get('/api/servers/')
    if servers_response.status_code != 200:
        print(f"❌ Error obteniendo servidores: {servers_response.status_code}")
        return False
    
    servers_data = json.loads(servers_response.content)
    if not servers_data.get('success') or not servers_data.get('data'):
        print("❌ No se encontraron servidores")
        return False
    
    # Buscar servidor con database auth o crear uno de prueba
    server = None
    for s in servers_data['data']:
        if s.get('auth_mode') in ['database', 'both']:
            server = s
            break
    
    if not server:
        print("⚠️  No se encontró servidor con auth_mode='database' o 'both'")
        print("   Creando servidor de prueba...")
        # Crear servidor de prueba
        server_obj = Server.objects.create(
            name="Test Server Email",
            host="test-server.local",
            rcon_port=25575,
            rcon_password="test123",
            minecraft_data_path="/data",
            auth_mode='database',
            is_active=True
        )
        # Asegurar que el usuario tenga acceso
        admin_user = User.objects.get(username=username)
        UserServerRole.objects.get_or_create(
            user=admin_user,
            server=server_obj,
            defaults={'role': 'admin'}
        )
        server = {'id': server_obj.id, 'name': server_obj.name}
        print(f"   ✅ Servidor de prueba creado: {server['name']} (ID: {server['id']})")
    else:
        print(f"✅ Servidor encontrado: {server['name']} (ID: {server['id']})")
    
    server_id = server['id']
    
    # 1. Admin crea usuario (sin contraseña)
    print("\n" + "=" * 60)
    print("🧪 TEST 1: Admin crea usuario (sin contraseña)")
    print("=" * 60)
    
    test_username = f"testuser_{os.getpid()}"
    test_email = f"test_{os.getpid()}@example.com"
    
    print(f"   Creando usuario: {test_username}")
    print(f"   Email: {test_email}")
    
    create_response = client.post(
        f'/api/servers/{server_id}/users/create/',
        json.dumps({
            'username': test_username,
            'email': test_email
        }),
        content_type='application/json'
    )
    
    print(f"   Status Code: {create_response.status_code}")
    
    if create_response.status_code != 200:
        print(f"   ❌ Error: {create_response.status_code}")
        print(create_response.content.decode())
        return False
    
    create_data = json.loads(create_response.content)
    if not create_data.get('success'):
        print(f"   ❌ Error: {create_data.get('error')}")
        return False
    
    print(f"   ✅ Usuario creado exitosamente!")
    print(f"   Mensaje: {create_data.get('message')}")
    
    user_data = create_data.get('data', {})
    user_id = user_data.get('id')
    print(f"   - ID: {user_id}")
    print(f"   - is_active: {user_data.get('is_active')} (debe ser False)")
    print(f"   - has_password_set: {user_data.get('has_password_set')} (debe ser False)")
    
    # Verificar en BD
    server_obj = Server.objects.get(id=server_id)
    user_obj = MinecraftUser.objects.get(id=user_id, server=server_obj)
    print(f"   ✅ Usuario verificado en BD")
    print(f"   - Email: {user_obj.email}")
    print(f"   - Token generado: {bool(user_obj.password_set_token)}")
    print(f"   - Token expira: {user_obj.password_set_token_expires}")
    
    if not user_obj.password_set_token:
        print(f"   ❌ Error: No se generó token")
        return False
    
    token = user_obj.password_set_token
    print(f"   ✅ Token obtenido: {token[:20]}...")
    
    # 2. Usuario establece contraseña con token
    print("\n" + "=" * 60)
    print("🧪 TEST 2: Usuario establece contraseña con token")
    print("=" * 60)
    
    test_password = "mypassword123"
    print(f"   Estableciendo contraseña para usuario: {test_username}")
    print(f"   Token: {token[:20]}...")
    
    set_password_response = client.post(
        f'/api/servers/{server_id}/users/set-password/',
        json.dumps({
            'token': token,
            'password': test_password
        }),
        content_type='application/json'
    )
    
    print(f"   Status Code: {set_password_response.status_code}")
    
    if set_password_response.status_code != 200:
        print(f"   ❌ Error: {set_password_response.status_code}")
        print(set_password_response.content.decode())
        return False
    
    set_password_data = json.loads(set_password_response.content)
    if not set_password_data.get('success'):
        print(f"   ❌ Error: {set_password_data.get('error')}")
        return False
    
    print(f"   ✅ Contraseña establecida exitosamente!")
    print(f"   Mensaje: {set_password_data.get('message')}")
    
    # Verificar en BD
    user_obj.refresh_from_db()
    print(f"   ✅ Usuario actualizado en BD")
    print(f"   - is_active: {user_obj.is_active} (debe ser True)")
    print(f"   - has_password_set: {user_obj.has_password_set()} (debe ser True)")
    print(f"   - Token limpiado: {not user_obj.password_set_token} (debe ser True)")
    
    if not user_obj.is_active:
        print(f"   ❌ Error: Usuario no está activo")
        return False
    
    if not user_obj.has_password_set():
        print(f"   ❌ Error: Contraseña no se estableció")
        return False
    
    # 3. Verificar que la contraseña funciona
    print("\n" + "=" * 60)
    print("🧪 TEST 3: Verificar autenticación con contraseña")
    print("=" * 60)
    
    if user_obj.check_password(test_password):
        print(f"   ✅ Contraseña verificada correctamente")
    else:
        print(f"   ❌ Error: La contraseña no se verificó")
        return False
    
    # 4. Probar autenticación completa
    authenticated_user = MinecraftUser.authenticate(server_obj, test_username, test_password)
    if authenticated_user:
        print(f"   ✅ Autenticación completa exitosa")
        print(f"   - Usuario: {authenticated_user.username}")
        print(f"   - last_login: {authenticated_user.last_login}")
    else:
        print(f"   ❌ Error: Autenticación falló")
        return False
    
    # 5. Limpiar - eliminar usuario de prueba
    print("\n" + "=" * 60)
    print("🧹 Limpiando usuario de prueba")
    print("=" * 60)
    
    user_obj.delete()
    print(f"   ✅ Usuario {test_username} eliminado")
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    print("✅ Flujo completo de registro por email testeado exitosamente")
    print("✅ Admin crea usuario sin contraseña")
    print("✅ Token generado y email preparado")
    print("✅ Usuario establece contraseña con token")
    print("✅ Usuario puede autenticarse correctamente")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    try:
        success = test_email_registration_flow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

