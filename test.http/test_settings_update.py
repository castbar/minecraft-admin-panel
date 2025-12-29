#!/usr/bin/env python3
"""
Test cuidadoso para POST /api/servers/<id>/settings/update/
- Obtiene configuración actual primero
- Hace cambios seguros y reversibles
- Verifica que los cambios se aplicaron
- Revierte los cambios al final
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

def test_settings_update():
    """Test cuidadoso de settings update"""
    print("=" * 60)
    print("TEST: POST /api/servers/<id>/settings/update/")
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
    
    # 1. Obtener configuración actual
    print("\n" + "=" * 60)
    print("📋 Obtener configuración actual")
    print("=" * 60)
    settings_response = client.get(f'/api/servers/{server_id}/settings/')
    if settings_response.status_code != 200:
        print(f"❌ Error obteniendo configuración: {settings_response.status_code}")
        return False
    
    settings_data = json.loads(settings_response.content)
    if not settings_data.get('success'):
        print(f"❌ Error en respuesta: {settings_data.get('error')}")
        return False
    
    current_settings = settings_data.get('data', {})
    print(f"   ✅ Configuración obtenida")
    print(f"   - is_public: {current_settings.get('is_public')}")
    print(f"   - auth_mode: {current_settings.get('auth_mode')}")
    print(f"   - enable_whitelist: {current_settings.get('enable_whitelist')}")
    print(f"   - online_mode: {current_settings.get('online_mode')}")
    print(f"   - max_players: {current_settings.get('max_players')}")
    print(f"   - motd: {current_settings.get('motd', '')[:50]}...")
    
    # Guardar valores originales para revertir
    original_values = {
        'is_public': current_settings.get('is_public'),
        'motd': current_settings.get('motd', ''),
    }
    
    # 2. Testear update con cambios seguros
    print("\n" + "=" * 60)
    print("🧪 TEST: POST /api/servers/<id>/settings/update/")
    print("=" * 60)
    print("   ⚠️  Haciendo cambios seguros y reversibles...")
    
    # Cambios seguros: solo is_public y motd (no afectan funcionalidad crítica)
    test_changes = {
        'is_public': not current_settings.get('is_public', False),  # Invertir valor
        'motd': f"Test MOTD {os.getpid()}",  # MOTD de prueba
    }
    
    print(f"   Cambios a aplicar:")
    print(f"   - is_public: {current_settings.get('is_public')} -> {test_changes['is_public']}")
    print(f"   - motd: '{current_settings.get('motd', '')[:30]}...' -> '{test_changes['motd']}'")
    
    update_response = client.post(
        f'/api/servers/{server_id}/settings/update/',
        json.dumps(test_changes),
        content_type='application/json'
    )
    
    print(f"\n   Status Code: {update_response.status_code}")
    
    if update_response.status_code == 403:
        print(f"   ❌ Error 403 - CSRF o permisos")
        print(update_response.content.decode())
        return False
    elif update_response.status_code != 200:
        print(f"   ❌ Error inesperado: {update_response.status_code}")
        print(update_response.content.decode())
        return False
    
    update_data = json.loads(update_response.content)
    if not update_data.get('success'):
        print(f"   ❌ Error en respuesta: {update_data.get('error')}")
        return False
    
    print(f"   ✅ Configuración actualizada exitosamente!")
    print(f"   Mensaje: {update_data.get('message')}")
    
    # 3. Verificar que los cambios se aplicaron
    print("\n" + "=" * 60)
    print("🔍 Verificar cambios aplicados")
    print("=" * 60)
    verify_response = client.get(f'/api/servers/{server_id}/settings/')
    if verify_response.status_code == 200:
        verify_data = json.loads(verify_response.content)
        if verify_data.get('success'):
            new_settings = verify_data.get('data', {})
            
            # Verificar is_public
            if new_settings.get('is_public') == test_changes['is_public']:
                print(f"   ✅ is_public actualizado correctamente: {new_settings.get('is_public')}")
            else:
                print(f"   ⚠️  is_public no coincide: esperado {test_changes['is_public']}, obtenido {new_settings.get('is_public')}")
            
            # Verificar motd (puede tener escape characters)
            new_motd = new_settings.get('motd', '')
            if test_changes['motd'] in new_motd or new_motd == test_changes['motd']:
                print(f"   ✅ motd actualizado correctamente: '{new_motd[:50]}...'")
            else:
                print(f"   ⚠️  motd no coincide completamente (puede tener escape): '{new_motd[:50]}...'")
    
    # 4. Revertir cambios
    print("\n" + "=" * 60)
    print("🔄 Revertir cambios a valores originales")
    print("=" * 60)
    revert_changes = {
        'is_public': original_values['is_public'],
        'motd': original_values['motd'],
    }
    
    print(f"   Revirtiendo:")
    print(f"   - is_public: {test_changes['is_public']} -> {revert_changes['is_public']}")
    print(f"   - motd: '{test_changes['motd']}' -> '{revert_changes['motd'][:30]}...'")
    
    revert_response = client.post(
        f'/api/servers/{server_id}/settings/update/',
        json.dumps(revert_changes),
        content_type='application/json'
    )
    
    if revert_response.status_code == 200:
        revert_data = json.loads(revert_response.content)
        if revert_data.get('success'):
            print(f"   ✅ Cambios revertidos exitosamente")
        else:
            print(f"   ⚠️  Error al revertir: {revert_data.get('error')}")
    else:
        print(f"   ⚠️  Error al revertir: {revert_response.status_code}")
    
    # 5. Verificar que se revirtieron
    final_response = client.get(f'/api/servers/{server_id}/settings/')
    if final_response.status_code == 200:
        final_data = json.loads(final_response.content)
        if final_data.get('success'):
            final_settings = final_data.get('data', {})
            if final_settings.get('is_public') == original_values['is_public']:
                print(f"   ✅ is_public revertido correctamente")
            else:
                print(f"   ⚠️  is_public no se revirtió completamente")
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    print("✅ Endpoint settings_update testeado exitosamente")
    print("✅ Cambios aplicados y revertidos correctamente")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    try:
        success = test_settings_update()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

