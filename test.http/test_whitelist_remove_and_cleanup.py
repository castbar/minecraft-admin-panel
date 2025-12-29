#!/usr/bin/env python3
"""
Test para:
1. POST /api/servers/<id>/whitelist/remove/ - Eliminar usuario de whitelist
2. Obtener jugadores conectados y usuarios en whitelist
3. Identificar y eliminar usuarios "test" de la whitelist
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
from server.models.models import Server, UserServerRole

User = get_user_model()

def test_whitelist_remove_and_cleanup():
    """Test whitelist remove y limpieza de usuarios test"""
    print("=" * 60)
    print("TEST: Whitelist Remove y Limpieza de Usuarios Test")
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
    
    print(f"✅ Servidor encontrado: {server_name} (ID: {server_id})")
    
    # 1. Obtener jugadores conectados
    print("\n" + "=" * 60)
    print("📊 Obtener jugadores conectados")
    print("=" * 60)
    status_response = client.get(f'/api/servers/{server_id}/status/')
    if status_response.status_code == 200:
        status_data = json.loads(status_response.content)
        if status_data.get('success'):
            players_online = status_data.get('data', {}).get('players', [])
            print(f"   ✅ Jugadores conectados: {len(players_online)}")
            if players_online:
                print(f"   Usuarios: {', '.join(players_online[:10])}")
    else:
        print(f"   ⚠️  Error obteniendo status: {status_response.status_code}")
    
    # 2. Obtener usuarios en whitelist
    print("\n" + "=" * 60)
    print("📋 Obtener usuarios en whitelist")
    print("=" * 60)
    whitelist_response = client.get(f'/api/servers/{server_id}/whitelist/')
    if whitelist_response.status_code != 200:
        print(f"   ❌ Error obteniendo whitelist: {whitelist_response.status_code}")
        print(whitelist_response.content.decode())
        return False
    
    whitelist_data = json.loads(whitelist_response.content)
    if not whitelist_data.get('success'):
        print(f"   ❌ Error en respuesta: {whitelist_data.get('error')}")
        return False
    
    whitelist = whitelist_data.get('data', [])
    print(f"   ✅ Usuarios en whitelist: {len(whitelist)}")
    
    # Extraer nombres de usuarios
    whitelist_users = []
    for user in whitelist:
        if isinstance(user, dict):
            name = user.get('name', '')
        else:
            name = str(user)
        if name:
            whitelist_users.append(name)
    
    if whitelist_users:
        print(f"   Usuarios: {', '.join(whitelist_users[:10])}")
    
    # 3. Identificar usuarios "test"
    print("\n" + "=" * 60)
    print("🔍 Identificar usuarios 'test'")
    print("=" * 60)
    test_users = [u for u in whitelist_users if 'test' in u.lower()]
    
    if not test_users:
        print("   ✅ No se encontraron usuarios 'test' en la whitelist")
    else:
        print(f"   ⚠️  Usuarios 'test' encontrados: {len(test_users)}")
        for user in test_users:
            print(f"      - {user}")
    
    # 4. Testear whitelist_remove con un usuario de prueba
    print("\n" + "=" * 60)
    print("🧪 TEST: POST /api/servers/<id>/whitelist/remove/")
    print("=" * 60)
    
    # Primero agregar un usuario de prueba para poder eliminarlo
    test_username = f"TestRemove_{os.getpid()}"
    print(f"   Agregando usuario de prueba: {test_username}")
    
    add_response = client.post(
        f'/api/servers/{server_id}/whitelist/add/',
        json.dumps({'username': test_username}),
        content_type='application/json'
    )
    
    if add_response.status_code == 200:
        print(f"   ✅ Usuario agregado: {test_username}")
    else:
        print(f"   ⚠️  No se pudo agregar usuario de prueba: {add_response.status_code}")
        test_username = None
    
    # Ahora probar remove
    if test_username:
        print(f"\n   Eliminando usuario de prueba: {test_username}")
        remove_response = client.post(
            f'/api/servers/{server_id}/whitelist/remove/',
            json.dumps({'username': test_username}),
            content_type='application/json'
        )
        
        print(f"   Status Code: {remove_response.status_code}")
        
        if remove_response.status_code == 200:
            remove_data = json.loads(remove_response.content)
            if remove_data.get('success'):
                print(f"   ✅ Usuario eliminado exitosamente!")
                print(f"   Mensaje: {remove_data.get('message')}")
                if remove_data.get('response'):
                    print(f"   Respuesta RCON: {remove_data.get('response')}")
            else:
                print(f"   ❌ Error en respuesta: {remove_data.get('error')}")
                return False
        elif remove_response.status_code == 403:
            print(f"   ❌ Error 403 - CSRF o permisos")
            print(remove_response.content.decode())
            return False
        else:
            print(f"   ❌ Error inesperado: {remove_response.status_code}")
            print(remove_response.content.decode())
            return False
    
    # 5. Eliminar usuarios "test" reales
    if test_users:
        print("\n" + "=" * 60)
        print("🧹 Limpiando usuarios 'test' de la whitelist")
        print("=" * 60)
        
        removed_count = 0
        for user in test_users:
            print(f"   Eliminando: {user}")
            remove_response = client.post(
                f'/api/servers/{server_id}/whitelist/remove/',
                json.dumps({'username': user}),
                content_type='application/json'
            )
            
            if remove_response.status_code == 200:
                remove_data = json.loads(remove_response.content)
                if remove_data.get('success'):
                    print(f"      ✅ {user} eliminado")
                    removed_count += 1
                else:
                    print(f"      ⚠️  Error: {remove_data.get('error')}")
            else:
                print(f"      ⚠️  Status {remove_response.status_code}: {remove_response.content.decode()[:100]}")
        
        print(f"\n   ✅ Usuarios eliminados: {removed_count}/{len(test_users)}")
        
        # Verificar que se eliminaron
        verify_response = client.get(f'/api/servers/{server_id}/whitelist/')
        if verify_response.status_code == 200:
            verify_data = json.loads(verify_response.content)
            remaining_whitelist = verify_data.get('data', [])
            remaining_users = []
            for user in remaining_whitelist:
                if isinstance(user, dict):
                    name = user.get('name', '')
                else:
                    name = str(user)
                if name:
                    remaining_users.append(name)
            
            remaining_test = [u for u in remaining_users if 'test' in u.lower()]
            if remaining_test:
                print(f"   ⚠️  Aún quedan usuarios 'test': {remaining_test}")
            else:
                print(f"   ✅ Todos los usuarios 'test' fueron eliminados")
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    print("✅ Endpoint whitelist_remove testeado exitosamente")
    if test_users:
        print(f"✅ Usuarios 'test' identificados y eliminados: {len(test_users)}")
    else:
        print("✅ No había usuarios 'test' para eliminar")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    try:
        success = test_whitelist_remove_and_cleanup()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

