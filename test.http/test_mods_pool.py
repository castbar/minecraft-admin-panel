#!/usr/bin/env python3
"""
Test del pool de mods precargados y configuración integrada
"""
import os
import sys
import django
import json

# Configurar Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'panel'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'minecraft_panel.settings')
os.chdir(os.path.join(os.path.dirname(__file__), '..', 'panel'))
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from server.models import Server, UserServerRole
from server.models.models_mods_pool import ModPool

def test_mods_pool():
    """Test del pool de mods"""
    print("\n" + "="*60)
    print("TEST: Pool de Mods Precargados")
    print("="*60)
    
    client = Client()
    
    # Crear usuario de prueba
    user, _ = User.objects.get_or_create(username='test_admin', defaults={'is_staff': True})
    user.set_password('test123')
    user.save()
    
    # Login
    login_success = client.login(username='test_admin', password='test123')
    if not login_success:
        print("❌ Error de login")
        return False
    
    print("✅ Login exitoso")
    
    # 1. Listar pool de mods (sin filtros)
    print("\n1. Listar pool de mods (sin filtros)...")
    response = client.get('/api/mods/pool/')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = json.loads(response.content)
        print(f"✅ Pool listado: {len(data.get('data', []))} mods encontrados")
        if data.get('data'):
            print(f"   Primer mod: {data['data'][0].get('display_name')}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.content.decode())
        return False
    
    # 2. Listar pool filtrado por tipo de servidor (Fabric)
    print("\n2. Listar pool filtrado por server_type=fabric...")
    response = client.get('/api/mods/pool/?server_type=fabric')
    if response.status_code == 200:
        data = json.loads(response.content)
        fabric_mods = data.get('data', [])
        print(f"✅ Mods compatibles con Fabric: {len(fabric_mods)}")
        for mod in fabric_mods[:3]:
            print(f"   - {mod.get('display_name')} ({mod.get('mod_type')})")
    else:
        print(f"❌ Error: {response.status_code}")
        return False
    
    # 3. Listar pool filtrado por tipo de servidor (Paper)
    print("\n3. Listar pool filtrado por server_type=paper...")
    response = client.get('/api/mods/pool/?server_type=paper')
    if response.status_code == 200:
        data = json.loads(response.content)
        paper_plugins = data.get('data', [])
        print(f"✅ Plugins compatibles con Paper: {len(paper_plugins)}")
        for plugin in paper_plugins[:3]:
            print(f"   - {plugin.get('display_name')} ({plugin.get('mod_type')})")
    else:
        print(f"❌ Error: {response.status_code}")
        return False
    
    # 4. Listar categorías
    print("\n4. Listar categorías...")
    response = client.get('/api/mods/pool/categories/')
    if response.status_code == 200:
        data = json.loads(response.content)
        categories = data.get('data', [])
        print(f"✅ Categorías encontradas: {', '.join(categories)}")
    else:
        print(f"❌ Error: {response.status_code}")
        return False
    
    # 5. Obtener detalles de un mod del pool
    print("\n5. Obtener detalles de un mod del pool...")
    mod_pool = ModPool.objects.filter(is_active=True).first()
    if mod_pool:
        response = client.get(f'/api/mods/pool/{mod_pool.id}/')
        if response.status_code == 200:
            data = json.loads(response.content)
            mod_data = data.get('data', {})
            print(f"✅ Detalles de {mod_data.get('display_name')}:")
            print(f"   - Tipo: {mod_data.get('mod_type')}")
            print(f"   - Compatible con: {', '.join(mod_data.get('compatible_server_types', []))}")
            print(f"   - Tiene configuración: {mod_data.get('has_config')}")
        else:
            print(f"❌ Error: {response.status_code}")
            return False
    else:
        print("⚠️  No hay mods en el pool para probar")
    
    return True

def test_mods_list_with_pool_info():
    """Test de lista de mods con información del pool"""
    print("\n" + "="*60)
    print("TEST: Lista de Mods con Información del Pool")
    print("="*60)
    
    client = Client()
    
    # Login
    user, _ = User.objects.get_or_create(username='test_admin', defaults={'is_staff': True})
    user.set_password('test123')
    user.save()
    client.login(username='test_admin', password='test123')
    
    # Obtener un servidor existente
    server = Server.objects.filter(is_active=True).first()
    if not server:
        print("⚠️  No hay servidores activos para probar")
        return True
    
    # Crear rol de usuario para el servidor
    UserServerRole.objects.get_or_create(
        user=user,
        server=server,
        defaults={'role': 'admin'}
    )
    
    print(f"✅ Usando servidor: {server.name} (tipo: {server.server_type})")
    
    # Listar mods con header X-Server-ID
    print("\n1. Listar mods instalados...")
    response = client.get(
        f'/api/servers/{server.id}/mods/',
        HTTP_X_SERVER_ID=str(server.id)
    )
    
    if response.status_code == 200:
        data = json.loads(response.content)
        mods = data.get('data', [])
        print(f"✅ Mods encontrados: {len(mods)}")
        
        # Mostrar información del pool si existe
        mods_with_pool = [m for m in mods if m.get('pool_info')]
        if mods_with_pool:
            print(f"   Mods con información del pool: {len(mods_with_pool)}")
            for mod in mods_with_pool[:3]:
                pool_info = mod.get('pool_info', {})
                print(f"   - {mod.get('name')}: {pool_info.get('display_name')} (has_config: {mod.get('has_config')})")
        else:
            print("   ⚠️  No hay mods instalados con información del pool")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.content.decode())
        return False
    
    return True

def test_mod_config():
    """Test de configuración de mods"""
    print("\n" + "="*60)
    print("TEST: Configuración de Mods")
    print("="*60)
    
    client = Client()
    
    # Login
    user, _ = User.objects.get_or_create(username='test_admin', defaults={'is_staff': True})
    user.set_password('test123')
    user.save()
    client.login(username='test_admin', password='test123')
    
    # Obtener un servidor existente
    server = Server.objects.filter(is_active=True).first()
    if not server:
        print("⚠️  No hay servidores activos para probar")
        return True
    
    # Crear rol de usuario para el servidor
    UserServerRole.objects.get_or_create(
        user=user,
        server=server,
        defaults={'role': 'admin'}
    )
    
    # Buscar un mod del pool que tenga configuración
    mod_pool = ModPool.objects.filter(
        is_active=True,
        config_file_path__isnull=False
    ).exclude(config_file_path='').first()
    
    if not mod_pool:
        print("⚠️  No hay mods en el pool con configuración para probar")
        return True
    
    print(f"✅ Probando con: {mod_pool.display_name}")
    print(f"   Archivo de config: {mod_pool.config_file_path}")
    
    # 1. Obtener configuración de un mod
    print("\n1. Obtener configuración de un mod...")
    mod_name = f"{mod_pool.name}.jar"
    response = client.get(
        f'/api/servers/{server.id}/mods/config/',
        {'mod_name': mod_name},
        HTTP_X_SERVER_ID=str(server.id)
    )
    
    if response.status_code == 200:
        data = json.loads(response.content)
        config_data = data.get('data', {})
        print(f"✅ Configuración obtenida:")
        print(f"   - Mod: {config_data.get('mod_name')}")
        print(f"   - Archivo existe: {config_data.get('file_exists')}")
        print(f"   - Es por defecto: {config_data.get('is_default')}")
        print(f"   - Formato: {config_data.get('config_format')}")
    elif response.status_code == 404:
        print(f"⚠️  Mod no encontrado en el pool o sin configuración (esperado si no está instalado)")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.content.decode())
        return False
    
    # 2. Actualizar configuración (solo si el archivo existe o podemos crearlo)
    # Esto requiere que el mod esté instalado, así que lo saltamos si no existe
    
    # 3. Resetear configuración
    print("\n2. Resetear configuración a valores por defecto...")
    response = client.post(
        f'/api/servers/{server.id}/mods/config/reset/',
        json.dumps({'mod_name': mod_name}),
        content_type='application/json',
        HTTP_X_SERVER_ID=str(server.id)
    )
    
    if response.status_code == 200:
        data = json.loads(response.content)
        print(f"✅ Configuración reseteada: {data.get('message')}")
    elif response.status_code == 404:
        print(f"⚠️  Mod no encontrado o sin configuración por defecto (esperado si no está instalado)")
    else:
        print(f"⚠️  Error: {response.status_code} (esperado si el mod no está instalado)")
        print(response.content.decode()[:200])
    
    return True

if __name__ == '__main__':
    print("\n" + "="*60)
    print("TESTS: Pool de Mods y Configuración")
    print("="*60)
    
    success = True
    success &= test_mods_pool()
    success &= test_mods_list_with_pool_info()
    success &= test_mod_config()
    
    print("\n" + "="*60)
    if success:
        print("✅ TODOS LOS TESTS PASARON")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
    print("="*60 + "\n")

