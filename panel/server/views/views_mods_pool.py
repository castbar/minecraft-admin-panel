"""
Vistas para gestionar el pool de mods precargados
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.conf import settings
import json
import os
from ..models.models_mods_pool import ModPool

@login_required
@require_http_methods(["GET"])
def mods_pool_list(request):
    """
    Listar mods/plugins del pool disponibles
    Filtra por tipo de servidor si se proporciona server_type
    """
    try:
        server_type = request.GET.get('server_type')
        category = request.GET.get('category')
        is_popular = request.GET.get('is_popular', '').lower() == 'true'
        is_recommended = request.GET.get('is_recommended', '').lower() == 'true'
        
        mods = ModPool.objects.filter(is_active=True)
        
        # Especificar solo los campos que necesitamos para evitar cargar file_path
        # que puede no existir en la base de datos
        mods = mods.only(
            'id', 'name', 'display_name', 'mod_type',
            'compatible_vanilla', 'compatible_fabric', 'compatible_forge',
            'compatible_bukkit', 'compatible_spigot', 'compatible_paper',
            'description', 'category', 'version',
            'is_popular', 'is_recommended',
            'config_file_path', 'config_format',
            'modrinth_id', 'curseforge_id', 'download_url'
        )
        
        # Filtrar por tipo de servidor
        if server_type:
            if server_type == 'vanilla':
                mods = mods.filter(compatible_vanilla=True)
            elif server_type == 'fabric':
                mods = mods.filter(compatible_fabric=True)
            elif server_type == 'forge':
                mods = mods.filter(compatible_forge=True)
            elif server_type == 'bukkit':
                mods = mods.filter(compatible_bukkit=True)
            elif server_type == 'spigot':
                mods = mods.filter(compatible_spigot=True)
            elif server_type == 'paper':
                mods = mods.filter(compatible_paper=True)
        
        # Filtrar por categoría
        if category:
            mods = mods.filter(category=category)
        
        # Filtrar populares
        if is_popular:
            mods = mods.filter(is_popular=True)
        
        # Filtrar recomendados
        if is_recommended:
            mods = mods.filter(is_recommended=True)
        
        mods = mods.order_by('-is_recommended', '-is_popular', 'display_name')
        
        data = []
        for m in mods:
            try:
                compatible_types = []
                try:
                    compatible_types = m.get_compatible_server_types()
                except Exception as e:
                    # Si falla get_compatible_server_types, construir manualmente
                    if m.compatible_vanilla:
                        compatible_types.append('vanilla')
                    if m.compatible_fabric:
                        compatible_types.append('fabric')
                    if m.compatible_forge:
                        compatible_types.append('forge')
                    if m.compatible_bukkit:
                        compatible_types.append('bukkit')
                    if m.compatible_spigot:
                        compatible_types.append('spigot')
                    if m.compatible_paper:
                        compatible_types.append('paper')
                
                mod_data = {
                    'id': m.id,
                    'name': m.name,
                    'display_name': m.display_name or m.name,
                    'mod_type': m.mod_type or 'mod',
                    'compatible_server_types': compatible_types,
                    'description': m.description or '',
                    'category': m.category or '',
                    'version': m.version or '',
                    'is_popular': bool(m.is_popular),
                    'is_recommended': bool(m.is_recommended),
                    'has_config': bool(m.config_file_path) if hasattr(m, 'config_file_path') else False,
                    'config_file_path': m.config_file_path or '' if hasattr(m, 'config_file_path') else '',
                    'config_format': m.config_format or 'json' if hasattr(m, 'config_format') else 'json',
                    'modrinth_id': m.modrinth_id or '',
                    'curseforge_id': m.curseforge_id or '',
                    'download_url': m.download_url or '',
                }
                # Solo agregar file_path si existe en el modelo
                if hasattr(m, 'file_path'):
                    mod_data['file_path'] = m.file_path or ''
                data.append(mod_data)
            except Exception as e:
                import traceback
                traceback.print_exc()
                # Continuar con el siguiente mod si hay error
                continue
        
        return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Error al cargar pool de mods: {str(e)}',
            'data': []
        }, status=500)

@login_required
@require_http_methods(["GET"])
def mods_pool_detail(request, mod_id):
    """
    Obtener detalles de un mod/plugin del pool
    Incluye configuración por defecto si existe
    """
    mod = get_object_or_404(ModPool, id=mod_id, is_active=True)
    
    return JsonResponse({
        'success': True,
        'data': {
            'id': mod.id,
            'name': mod.name,
            'display_name': mod.display_name,
            'mod_type': mod.mod_type,
            'compatible_server_types': mod.get_compatible_server_types(),
            'description': mod.description,
            'category': mod.category,
            'version': mod.version,
            'is_popular': mod.is_popular,
            'is_recommended': mod.is_recommended,
            'config_file_path': mod.config_file_path,
            'config_format': mod.config_format,
            'default_config': mod.default_config,
            'has_config': bool(mod.config_file_path),
            'modrinth_id': mod.modrinth_id,
            'curseforge_id': mod.curseforge_id,
            'download_url': mod.download_url,
        }
    })

@login_required
@require_http_methods(["GET"])
def mods_pool_categories(request):
    """
    Listar categorías disponibles en el pool
    """
    categories = ModPool.objects.filter(
        is_active=True
    ).exclude(
        category=''
    ).values_list('category', flat=True).distinct()
    
    return JsonResponse({
        'success': True,
        'data': sorted(list(categories))
    })

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def mods_pool_install(request, server_id=None):
    """
    Instalar un mod del pool en un servidor - Requiere header X-Server-ID
    
    Body JSON:
    {
        "mod_pool_id": 1
    }
    
    Copia el archivo del pool al servidor
    """
    from ..utils.permissions import _get_server_id_from_request
    from ..models import Server, UserServerRole
    from django.conf import settings
    import shutil
    import docker
    
    # Obtener server_id del header
    resolved_server_id = _get_server_id_from_request(request) or server_id
    if not resolved_server_id:
        return JsonResponse({
            'success': False, 
            'error': 'Server ID required. Send header X-Server-ID: <id>'
        }, status=400)
    
    try:
        server = get_object_or_404(Server, id=resolved_server_id, is_active=True)
    except Server.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Server not found'}, status=404)
    
    # Verificar permisos
    user_role = UserServerRole.objects.filter(user=request.user, server=server).first()
    if not user_role:
        return JsonResponse({'success': False, 'error': 'No access to this server'}, status=403)
    
    if not user_role.has_permission('manage_mods'):
        return JsonResponse({'success': False, 'error': 'Permission denied: manage_mods required'}, status=403)
    
    try:
        data = json.loads(request.body)
        mod_pool_id = data.get('mod_pool_id')
        
        if not mod_pool_id:
            return JsonResponse({'success': False, 'error': 'mod_pool_id required'}, status=400)
        
        mod_pool = get_object_or_404(ModPool, id=mod_pool_id, is_active=True)
        
        # Verificar compatibilidad
        compatible_types = mod_pool.get_compatible_server_types()
        if server.server_type not in compatible_types:
            return JsonResponse({
                'success': False, 
                'error': f'Mod {mod_pool.display_name} is not compatible with server type {server.server_type}. Compatible types: {", ".join(compatible_types)}'
            }, status=400)
        
        # Buscar archivo del mod
        mods_pool_path = getattr(settings, 'MODS_POOL_PATH', '/data/mods_pool')
        
        # Si tiene file_path configurado, usarlo (verificar si existe primero)
        source_file = None
        if hasattr(mod_pool, 'file_path') and mod_pool.file_path:
            try:
                if os.path.exists(mod_pool.file_path):
                    source_file = mod_pool.file_path
            except:
                pass
        else:
            # Buscar por nombre común
            possible_names = [
                f'{mod_pool.name}.jar',
                f'{mod_pool.display_name.lower().replace(" ", "-")}.jar',
                f'{mod_pool.name}-{mod_pool.version}.jar' if mod_pool.version else None,
            ]
            
            source_file = None
            for name in possible_names:
                if name:
                    test_path = os.path.join(mods_pool_path, name)
                    if os.path.exists(test_path):
                        source_file = test_path
                        break
            
            if not source_file:
                return JsonResponse({
                    'success': False,
                    'error': f'Mod file not found. Please place {mod_pool.name}.jar in {mods_pool_path}/'
                }, status=404)
        
        # Determinar carpeta destino según tipo de servidor
        if server.server_type in ['bukkit', 'spigot', 'paper']:
            dest_folder = 'plugins'
        else:
            dest_folder = 'mods'
        
        # Nombre del archivo destino
        dest_filename = f'{mod_pool.name}.jar'
        
        # Si el servidor tiene container_name, copiar al contenedor
        if server.container_name:
            try:
                client = docker.from_env()
                container = client.containers.get(server.container_name)
                
                dest_path = f'/data/{dest_folder}/{dest_filename}'
                
                # Verificar si ya existe
                result = container.exec_run(f'sh -c "test -f {dest_path} && echo exists || echo notfound"', user='minecraft')
                if result.output.decode('utf-8').strip() == 'exists':
                    return JsonResponse({
                        'success': False,
                        'error': f'Mod {dest_filename} already installed'
                    }, status=400)
                
                # Copiar archivo al contenedor
                import tarfile
                import io
                
                with open(source_file, 'rb') as f:
                    file_content = f.read()
                
                tar_stream = io.BytesIO()
                with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                    tarinfo = tarfile.TarInfo(name=dest_filename)
                    tarinfo.size = len(file_content)
                    tar.addfile(tarinfo, io.BytesIO(file_content))
                
                tar_stream.seek(0)
                container.put_archive(f'/data/{dest_folder}', tar_stream.read())
                
                # Asegurar permisos
                container.exec_run(f'chown minecraft:minecraft {dest_path}', user='root')
                
                return JsonResponse({
                    'success': True,
                    'message': f'Mod {mod_pool.display_name} installed successfully',
                    'data': {
                        'name': dest_filename,
                        'enabled': True
                    }
                })
            except Exception as e:
                import traceback
                traceback.print_exc()
                return JsonResponse({
                    'success': False,
                    'error': f'Error installing to container: {str(e)}'
                }, status=500)
        
        # Método original: copiar a filesystem local
        dest_path = os.path.join(server.minecraft_data_path, dest_folder, dest_filename)
        
        if os.path.exists(dest_path):
            return JsonResponse({
                'success': False,
                'error': f'Mod {dest_filename} already installed'
            }, status=400)
        
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(source_file, dest_path)
        
        return JsonResponse({
            'success': True,
            'message': f'Mod {mod_pool.display_name} installed successfully',
            'data': {
                'name': dest_filename,
                'enabled': True
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def mods_pool_create(request):
    """
    Crear nuevo mod/plugin en el pool (requiere staff)
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permission denied: Staff only'}, status=403)
    
    try:
        data = json.loads(request.body)
        
        mod = ModPool.objects.create(
            name=data.get('name', '').strip(),
            display_name=data.get('display_name', '').strip(),
            mod_type=data.get('mod_type', 'mod'),
            compatible_vanilla=data.get('compatible_vanilla', False),
            compatible_fabric=data.get('compatible_fabric', False),
            compatible_forge=data.get('compatible_forge', False),
            compatible_bukkit=data.get('compatible_bukkit', False),
            compatible_spigot=data.get('compatible_spigot', False),
            compatible_paper=data.get('compatible_paper', False),
            description=data.get('description', ''),
            category=data.get('category', ''),
            version=data.get('version', ''),
            is_popular=data.get('is_popular', False),
            is_recommended=data.get('is_recommended', False),
            config_file_path=data.get('config_file_path', ''),
            config_format=data.get('config_format', 'json'),
            default_config=data.get('default_config', ''),
            modrinth_id=data.get('modrinth_id', ''),
            curseforge_id=data.get('curseforge_id', ''),
            download_url=data.get('download_url', ''),
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Mod {mod.display_name} added to pool',
            'data': {
                'id': mod.id,
                'name': mod.name,
                'display_name': mod.display_name,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

