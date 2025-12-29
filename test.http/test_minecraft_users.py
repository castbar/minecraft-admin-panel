#!/usr/bin/env python3
"""
Test para endpoints de usuarios de Minecraft
- Verifica que los endpoints funcionan correctamente
- Verifica el comportamiento cuando auth_mode no es 'database' o 'both'
- Si el servidor tiene auth_mode correcto, prueba crear/actualizar/eliminar usuarios
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

User = get_user_model()

def test_minecraft_users():
    """Test de endpoints de usuarios de Minecraft"""
    print("=" * 60)
    print("TEST: Endpoints de Usuarios de Minecraft")
    print("=" * 60)
    
    client = Client()
    
    # Login
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
    
    # Obtener servidor
    servers_response = client.get('/api/servers/')
    if servers_response.status_code != 200:
        print(f"❌ Error obteniendo servidores: {servers_response.status_code}")
        return False
    
    servers_data = json.loads(servers_response.content)
    if not servers_data.get('success') or not servers_data.get('data'):
        print("❌ No se encontraron servidores")
        return False
    
    server = servers_data['data'][0]
    server_id = server['id']
    server_name = server['name']
    auth_mode = server.get('auth_mode', 'whitelist')
    
    print(f"✅ Servidor encontrado: {server_name} (ID: {server_id})")
    print(f"   auth_mode: {auth_mode}")
    
    # 1. Test GET /api/servers/<id>/users/
    print("\n" + "=" * 60)
    print("🧪 TEST 1: GET /api/servers/<id>/users/")
    print("=" * 60)
    
    users_list_response = client.get(f'/api/servers/{server_id}/users/')
    print(f"   Status Code: {users_list_response.status_code}")
    
    if users_list_response.status_code == 400:
        error_data = json.loads(users_list_response.content)
        if 'database authentication' in error_data.get('error', '').lower():
            print(f"   ✅ Comportamiento esperado: Servidor no usa autenticación por BD")
            print(f"   Error: {error_data.get('error')}")
        else:
            print(f"   ⚠️  Error inesperado: {error_data.get('error')}")
    elif users_list_response.status_code == 200:
        users_data = json.loads(users_list_response.content)
        if users_data.get('success'):
            users = users_data.get('data', [])
            print(f"   ✅ Usuarios encontrados: {len(users)}")
            for user in users[:5]:
                print(f"      - {user.get('username')} (activo: {user.get('is_active')})")
        else:
            print(f"   ❌ Error: {users_data.get('error')}")
    else:
        print(f"   ❌ Error inesperado: {users_list_response.status_code}")
        print(users_list_response.content.decode())
    
    # 2. Test POST /api/servers/<id>/users/create/
    print("\n" + "=" * 60)
    print("🧪 TEST 2: POST /api/servers/<id>/users/create/")
    print("=" * 60)
    
    test_username = f"testuser_{os.getpid()}"
    test_password = "testpass123"
    
    print(f"   Intentando crear usuario: {test_username}")
    
    create_response = client.post(
        f'/api/servers/{server_id}/users/create/',
        json.dumps({
            'username': test_username,
            'password': test_password
        }),
        content_type='application/json'
    )
    
    print(f"   Status Code: {create_response.status_code}")
    
    if create_response.status_code == 400:
        error_data = json.loads(create_response.content)
        if 'database authentication' in error_data.get('error', '').lower():
            print(f"   ✅ Comportamiento esperado: Servidor no usa autenticación por BD")
            print(f"   Error: {error_data.get('error')}")
        else:
            print(f"   ⚠️  Error de validación: {error_data.get('error')}")
    elif create_response.status_code == 403:
        print(f"   ❌ Error 403 - CSRF o permisos")
        print(create_response.content.decode())
    elif create_response.status_code == 200:
        create_data = json.loads(create_response.content)
        if create_data.get('success'):
            print(f"   ✅ Usuario creado exitosamente!")
            print(f"   ID: {create_data.get('data', {}).get('id')}")
            print(f"   Username: {create_data.get('data', {}).get('username')}")
            
            # Verificar que el usuario existe en la BD
            server_obj = Server.objects.get(id=server_id)
            user_obj = MinecraftUser.objects.filter(server=server_obj, username=test_username).first()
            if user_obj:
                print(f"   ✅ Usuario verificado en BD")
                print(f"   - Password hash existe: {bool(user_obj.password_hash)}")
                print(f"   - Salt existe: {bool(user_obj.salt)}")
                
                # Verificar que la contraseña funciona
                if user_obj.check_password(test_password):
                    print(f"   ✅ Contraseña verificada correctamente")
                else:
                    print(f"   ❌ Error: La contraseña no se verificó correctamente")
                
                # Guardar ID para tests siguientes
                test_user_id = user_obj.id
            else:
                print(f"   ❌ Error: Usuario no encontrado en BD")
                return False
        else:
            print(f"   ❌ Error: {create_data.get('error')}")
    else:
        print(f"   ❌ Error inesperado: {create_response.status_code}")
        print(create_response.content.decode())
    
    # 3. Test POST /api/servers/<id>/users/<user_id>/update/ (solo si se creó el usuario)
    if create_response.status_code == 200 and 'test_user_id' in locals():
        print("\n" + "=" * 60)
        print("🧪 TEST 3: POST /api/servers/<id>/users/<user_id>/update/")
        print("=" * 60)
        
        new_password = "newpass456"
        print(f"   Actualizando contraseña del usuario {test_username}")
        
        update_response = client.post(
            f'/api/servers/{server_id}/users/{test_user_id}/update/',
            json.dumps({
                'password': new_password
            }),
            content_type='application/json'
        )
        
        print(f"   Status Code: {update_response.status_code}")
        
        if update_response.status_code == 200:
            update_data = json.loads(update_response.content)
            if update_data.get('success'):
                print(f"   ✅ Usuario actualizado exitosamente!")
                
                # Verificar que la nueva contraseña funciona
                user_obj.refresh_from_db()
                if user_obj.check_password(new_password):
                    print(f"   ✅ Nueva contraseña verificada correctamente")
                else:
                    print(f"   ❌ Error: La nueva contraseña no se verificó")
        else:
            print(f"   ⚠️  Error: {update_response.status_code}")
            print(update_response.content.decode())
        
        # 4. Test DELETE /api/servers/<id>/users/<user_id>/delete/
        print("\n" + "=" * 60)
        print("🧪 TEST 4: DELETE /api/servers/<id>/users/<user_id>/delete/")
        print("=" * 60)
        
        print(f"   Eliminando usuario {test_username}")
        
        delete_response = client.delete(f'/api/servers/{server_id}/users/{test_user_id}/delete/')
        
        print(f"   Status Code: {delete_response.status_code}")
        
        if delete_response.status_code == 200:
            delete_data = json.loads(delete_response.content)
            if delete_data.get('success'):
                print(f"   ✅ Usuario eliminado exitosamente!")
                
                # Verificar que el usuario ya no existe
                user_obj = MinecraftUser.objects.filter(server=server_obj, username=test_username).first()
                if not user_obj:
                    print(f"   ✅ Usuario verificado como eliminado en BD")
                else:
                    print(f"   ❌ Error: Usuario aún existe en BD")
        else:
            print(f"   ⚠️  Error: {delete_response.status_code}")
            print(delete_response.content.decode())
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    print("✅ Endpoints de usuarios de Minecraft revisados")
    if auth_mode not in ['database', 'both']:
        print(f"ℹ️  Servidor usa auth_mode='{auth_mode}', por lo que estos endpoints retornan 400 (comportamiento esperado)")
        print("ℹ️  Para probar completamente, cambiar auth_mode a 'database' o 'both'")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    try:
        success = test_minecraft_users()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

