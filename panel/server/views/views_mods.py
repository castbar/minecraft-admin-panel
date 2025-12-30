"""
Vistas para gestionar mods de Minecraft
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
import json
import os
import shutil
from ..models import Server, UserServerRole
from ..models.models_mods_pool import ModPool
from ..utils.permissions import _get_server_id_from_request, require_server_permission

def _get_rcon_connection(server):
    """Conectar a RCON para un servidor específico"""
    try:
        import mcrcon
        rcon = mcrcon.MCRcon(server.host, server.rcon_password, port=server.rcon_port)
        rcon.connect()
        return rcon
    except Exception as e:
        print(f"RCON Error for {server.name}: {str(e)}")
        return None

@login_required
@require_http_methods(["GET"])
def mods_list(request, server_id=None):
    """
    Listar mods instalados - Requiere header X-Server-ID
    
    Retorna lista de mods con información de si están habilitados o no.
    Un mod está deshabilitado si tiene extensión .disabled o está en carpeta mods-disabled/
    Incluye información de configuración si existe.
    """
    # Obtener server_id del header (método principal) o de la URL (compatibilidad)
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
    
    # Si el servidor tiene container_name, leer desde el contenedor
    if server.container_name:
        import docker
        try:
            client = docker.from_env()
            container = client.containers.get(server.container_name)
            
            # Ejecutar comando para listar mods en el contenedor
            mods_path = '/data/mods'
            plugins_path = '/data/plugins'
            
            # Determinar carpeta según tipo de servidor
            if server.server_type in ['bukkit', 'spigot', 'paper']:
                install_path = plugins_path
            else:
                install_path = mods_path
            
            # Listar archivos en el contenedor - usar sh -c para que funcionen redirecciones
            result = container.exec_run(f'sh -c "ls -1 {install_path} 2>/dev/null || echo \\"\\""', user='minecraft')
            files_str = result.output.decode('utf-8').strip()
            # Filtrar solo archivos .jar y limpiar líneas vacías
            files = [f.strip() for f in files_str.split('\n') if f.strip() and f.strip().endswith('.jar')] if files_str else []
            
            mods = []
            for file in files:
                # Obtener tamaño del archivo
                size_result = container.exec_run(f'stat -c%s {install_path}/{file}', user='minecraft')
                size = 0
                try:
                    size_str = size_result.output.decode('utf-8').strip()
                    if size_str and size_str.isdigit():
                        size = int(size_str)
                except:
                    size = 0
                
                # Buscar en pool de mods - búsqueda exacta del nombre (ignorando extensión)
                # Limpiar solo la extensión .jar o .disabled
                clean_name = file.replace('.jar', '').replace('.disabled', '').strip()
                
                # Búsqueda exacta (case-insensitive)
                mod_pool = ModPool.objects.filter(name__iexact=clean_name).first()
                
                mod_info = {
                    'name': file,
                    'enabled': True,
                    'size': size,
                    'size_mb': round(size / (1024 * 1024), 2) if size > 0 else 0,
                    'path': 'mods' if server.server_type not in ['bukkit', 'spigot', 'paper'] else 'plugins',
                    'has_config': False,
                    'file_path': f'{install_path}/{file}',
                }
                
                # Agregar información del pool si existe
                if mod_pool:
                    mod_info['pool_info'] = {
                        'id': mod_pool.id,
                        'display_name': mod_pool.display_name,
                        'mod_type': mod_pool.mod_type,
                        'category': mod_pool.category,
                        'has_config': bool(mod_pool.config_file_path),
                        'config_file_path': mod_pool.config_file_path,
                        'config_format': mod_pool.config_format,
                    }
                    mod_info['has_config'] = bool(mod_pool.config_file_path)
                
                mods.append(mod_info)
            
            return JsonResponse({'success': True, 'data': mods})
        except Exception as e:
            import traceback
            traceback.print_exc()
            # Continuar con método de filesystem si falla
    
    # Método original: leer desde filesystem local
    mods_path = os.path.join(server.minecraft_data_path, 'mods')
    mods_disabled_path = os.path.join(server.minecraft_data_path, 'mods-disabled')
    plugins_path = os.path.join(server.minecraft_data_path, 'plugins')
    
    # Determinar carpeta según tipo de servidor
    if server.server_type in ['bukkit', 'spigot', 'paper']:
        # Plugins van en carpeta plugins/
        install_path = plugins_path
    else:
        # Mods van en carpeta mods/
        install_path = mods_path
    
    mods = []
    
    # Listar mods/plugins habilitados
    if os.path.exists(install_path):
        for file in os.listdir(install_path):
            if file.endswith('.jar'):
                file_path = os.path.join(install_path, file)
                size = os.path.getsize(file_path)
                
                # Buscar en pool de mods
                mod_pool = ModPool.objects.filter(name__iexact=file.replace('.jar', '')).first()
                mod_info = {
                    'name': file,
                    'enabled': True,
                    'size': size,
                    'size_mb': round(size / (1024 * 1024), 2),
                    'path': 'mods' if server.server_type not in ['bukkit', 'spigot', 'paper'] else 'plugins',
                    'has_config': False,
                }
                
                # Agregar información del pool si existe
                if mod_pool:
                    mod_info['pool_info'] = {
                        'id': mod_pool.id,
                        'display_name': mod_pool.display_name,
                        'mod_type': mod_pool.mod_type,
                        'category': mod_pool.category,
                        'has_config': bool(mod_pool.config_file_path),
                        'config_file_path': mod_pool.config_file_path,
                        'config_format': mod_pool.config_format,
                    }
                    mod_info['has_config'] = bool(mod_pool.config_file_path)
                
                mods.append(mod_info)
    
    # Listar mods deshabilitados (solo para mods, no plugins)
    if server.server_type not in ['bukkit', 'spigot', 'paper']:
        if os.path.exists(mods_disabled_path):
            for file in os.listdir(mods_disabled_path):
                if file.endswith('.jar') or file.endswith('.jar.disabled'):
                    file_path = os.path.join(mods_disabled_path, file)
                    display_name = file.replace('.disabled', '')
                    size = os.path.getsize(file_path)
                    
                    mod_pool = ModPool.objects.filter(name__iexact=display_name.replace('.jar', '')).first()
                    mod_info = {
                        'name': display_name,
                        'enabled': False,
                        'size': size,
                        'size_mb': round(size / (1024 * 1024), 2),
                        'path': 'mods-disabled',
                        'has_config': False,
                    }
                    
                    if mod_pool:
                        mod_info['pool_info'] = {
                            'id': mod_pool.id,
                            'display_name': mod_pool.display_name,
                            'mod_type': mod_pool.mod_type,
                            'category': mod_pool.category,
                            'has_config': bool(mod_pool.config_file_path),
                            'config_file_path': mod_pool.config_file_path,
                            'config_format': mod_pool.config_format,
                        }
                        mod_info['has_config'] = bool(mod_pool.config_file_path)
                    
                    mods.append(mod_info)
        
        # Buscar mods con .disabled en carpeta mods/
        if os.path.exists(mods_path):
            for file in os.listdir(mods_path):
                if file.endswith('.jar.disabled'):
                    file_path = os.path.join(mods_path, file)
                    display_name = file.replace('.disabled', '')
                    size = os.path.getsize(file_path)
                    
                    mod_pool = ModPool.objects.filter(name__iexact=display_name.replace('.jar', '')).first()
                    mod_info = {
                        'name': display_name,
                        'enabled': False,
                        'size': size,
                        'size_mb': round(size / (1024 * 1024), 2),
                        'path': 'mods',
                        'has_config': False,
                    }
                    
                    if mod_pool:
                        mod_info['pool_info'] = {
                            'id': mod_pool.id,
                            'display_name': mod_pool.display_name,
                            'mod_type': mod_pool.mod_type,
                            'category': mod_pool.category,
                            'has_config': bool(mod_pool.config_file_path),
                            'config_file_path': mod_pool.config_file_path,
                            'config_format': mod_pool.config_format,
                        }
                        mod_info['has_config'] = bool(mod_pool.config_file_path)
                    
                    mods.append(mod_info)
    
    return JsonResponse({'success': True, 'data': mods})

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def mod_enable(request, server_id=None):
    """
    Habilitar un mod - Requiere header X-Server-ID
    
    Body JSON:
    {
        "mod_name": "example-mod.jar"
    }
    
    Habilita un mod moviéndolo de mods-disabled/ a mods/ o removiendo .disabled
    """
    # Obtener server_id del header (método principal) o de la URL (compatibilidad)
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
        mod_name = data.get('mod_name', '').strip()
        
        if not mod_name:
            return JsonResponse({'success': False, 'error': 'Mod name required'}, status=400)
        
        # Validar que es un nombre de archivo seguro
        if '..' in mod_name or '/' in mod_name or '\\' in mod_name:
            return JsonResponse({'success': False, 'error': 'Invalid mod name'}, status=400)
        
        mods_path = os.path.join(server.minecraft_data_path, 'mods')
        mods_disabled_path = os.path.join(server.minecraft_data_path, 'mods-disabled')
        os.makedirs(mods_path, exist_ok=True)
        os.makedirs(mods_disabled_path, exist_ok=True)
        
        # Buscar el mod deshabilitado
        # Opción 1: En carpeta mods-disabled/
        disabled_file_path = os.path.join(mods_disabled_path, mod_name)
        if not os.path.exists(disabled_file_path):
            # Opción 2: Con extensión .disabled en carpeta mods/
            disabled_file_path = os.path.join(mods_path, f"{mod_name}.disabled")
        
        if not os.path.exists(disabled_file_path):
            return JsonResponse({'success': False, 'error': 'Mod not found or already enabled'}, status=404)
        
        # Mover/renombrar a carpeta mods/ sin .disabled
        target_path = os.path.join(mods_path, mod_name)
        
        # Si el archivo ya existe habilitado, error
        if os.path.exists(target_path):
            return JsonResponse({'success': False, 'error': 'Mod already enabled'}, status=400)
        
        # Mover archivo
        shutil.move(disabled_file_path, target_path)
        
        return JsonResponse({
            'success': True, 
            'message': f'Mod {mod_name} enabled',
            'data': {
                'name': mod_name,
                'enabled': True
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def mod_disable(request, server_id=None):
    """
    Deshabilitar un mod - Requiere header X-Server-ID
    
    Body JSON:
    {
        "mod_name": "example-mod.jar"
    }
    
    Deshabilita un mod moviéndolo a mods-disabled/ o agregando .disabled
    """
    # Obtener server_id del header (método principal) o de la URL (compatibilidad)
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
        mod_name = data.get('mod_name', '').strip()
        
        if not mod_name:
            return JsonResponse({'success': False, 'error': 'Mod name required'}, status=400)
        
        # Validar que es un nombre de archivo seguro
        if '..' in mod_name or '/' in mod_name or '\\' in mod_name:
            return JsonResponse({'success': False, 'error': 'Invalid mod name'}, status=400)
        
        mods_path = os.path.join(server.minecraft_data_path, 'mods')
        mods_disabled_path = os.path.join(server.minecraft_data_path, 'mods-disabled')
        os.makedirs(mods_path, exist_ok=True)
        os.makedirs(mods_disabled_path, exist_ok=True)
        
        # Buscar el mod habilitado
        mod_file_path = os.path.join(mods_path, mod_name)
        
        if not os.path.exists(mod_file_path):
            return JsonResponse({'success': False, 'error': 'Mod not found or already disabled'}, status=404)
        
        # Mover a carpeta mods-disabled/
        target_path = os.path.join(mods_disabled_path, mod_name)
        
        # Si el archivo ya existe en disabled, error
        if os.path.exists(target_path):
            return JsonResponse({'success': False, 'error': 'Mod already disabled'}, status=400)
        
        # Mover archivo
        shutil.move(mod_file_path, target_path)
        
        return JsonResponse({
            'success': True, 
            'message': f'Mod {mod_name} disabled',
            'data': {
                'name': mod_name,
                'enabled': False
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def mod_upload(request, server_id=None):
    """
    Subir un nuevo mod - Requiere header X-Server-ID
    
    Form data:
    - mod_file: archivo .jar
    
    Sube un mod a la carpeta mods/ (habilitado por defecto)
    """
    # Obtener server_id del header (método principal) o de la URL (compatibilidad)
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
        if 'mod_file' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No file provided'}, status=400)
        
        file = request.FILES['mod_file']
        if not file.name.endswith('.jar'):
            return JsonResponse({'success': False, 'error': 'Only .jar files allowed'}, status=400)
        
        # Validar tamaño (max 200MB)
        if file.size > 200 * 1024 * 1024:
            return JsonResponse({'success': False, 'error': 'File too large (max 200MB)'}, status=400)
        
        # Si el servidor tiene container_name, guardar en el contenedor del servidor
        if server.container_name:
            import docker
            try:
                client = docker.from_env()
                container = client.containers.get(server.container_name)
                
                mods_path = '/data/mods'
                
                # Verificar si el archivo ya existe
                result = container.exec_run(f'test -f {mods_path}/{file.name} && echo "exists" || echo ""', user='minecraft')
                if result.output.decode('utf-8').strip() == 'exists':
                    return JsonResponse({'success': False, 'error': f'Mod {file.name} already exists'}, status=400)
                
                # Crear directorio si no existe
                container.exec_run(f'mkdir -p {mods_path}', user='minecraft')
                
                # Guardar archivo temporalmente en el contenedor Django
                import tempfile
                import tarfile
                import io
                
                # Leer el contenido del archivo
                file_content = b''
                for chunk in file.chunks():
                    file_content += chunk
                
                # Crear un tar en memoria
                tar_stream = io.BytesIO()
                with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                    tarinfo = tarfile.TarInfo(name=file.name)
                    tarinfo.size = len(file_content)
                    tar.addfile(tarinfo, io.BytesIO(file_content))
                
                tar_stream.seek(0)
                
                # Copiar archivo al contenedor del servidor usando put_archive
                container.put_archive(mods_path, tar_stream.read())
                
                # Asegurar permisos correctos
                container.exec_run(f'chown minecraft:minecraft {mods_path}/{file.name}', user='root')
                
                return JsonResponse({
                    'success': True, 
                    'message': f'Mod {file.name} uploaded successfully',
                    'data': {
                        'name': file.name,
                        'enabled': True,
                        'size': file.size,
                        'size_mb': round(file.size / (1024 * 1024), 2)
                    }
                })
            except Exception as e:
                import traceback
                traceback.print_exc()
                return JsonResponse({'success': False, 'error': f'Error uploading to container: {str(e)}'}, status=500)
        
        # Método original: guardar en filesystem local
        mods_path = os.path.join(server.minecraft_data_path, 'mods')
        os.makedirs(mods_path, exist_ok=True)
        
        mod_path = os.path.join(mods_path, file.name)
        
        # Si el archivo ya existe, error
        if os.path.exists(mod_path):
            return JsonResponse({'success': False, 'error': f'Mod {file.name} already exists'}, status=400)
        
        with open(mod_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        
        return JsonResponse({
            'success': True, 
            'message': f'Mod {file.name} uploaded successfully',
            'data': {
                'name': file.name,
                'enabled': True,
                'size': file.size,
                'size_mb': round(file.size / (1024 * 1024), 2)
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def mod_delete(request, server_id=None):
    """
    Eliminar un mod - Requiere header X-Server-ID
    
    Body JSON:
    {
        "mod_name": "example-mod.jar"
    }
    
    Elimina un mod completamente (habilitado o deshabilitado)
    """
    # Obtener server_id del header (método principal) o de la URL (compatibilidad)
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
        mod_name = data.get('mod_name', '').strip()
        file_path = data.get('file_path', '').strip()
        enabled = data.get('enabled', True)
        
        if not mod_name:
            return JsonResponse({'success': False, 'error': 'Mod name required'}, status=400)
        
        # Validar que es un nombre de archivo seguro
        if '..' in mod_name or '/' in mod_name or '\\' in mod_name:
            return JsonResponse({'success': False, 'error': 'Invalid mod name'}, status=400)
        
        # Si el servidor tiene container_name, eliminar del contenedor del servidor
        if server.container_name:
            import docker
            try:
                client = docker.from_env()
                container = client.containers.get(server.container_name)
                
                # Si tenemos file_path completo, usarlo directamente
                if file_path:
                    # Limpiar la ruta (remover /data/ si está al inicio)
                    clean_path = file_path.replace('/data/', '').lstrip('/')
                    full_path = f'/data/{clean_path}'
                    
                    # Verificar que existe usando sh -c
                    result = container.exec_run(f'sh -c "test -f {full_path} && echo exists || echo notfound"', user='minecraft')
                    output = result.output.decode('utf-8').strip()
                    if output == 'exists':
                        container.exec_run(f'rm {full_path}', user='minecraft')
                        return JsonResponse({
                            'success': True, 
                            'message': f'Mod {mod_name} deleted'
                        })
                
                # Si no tenemos file_path, buscar en ubicaciones comunes
                mods_path = '/data/mods'
                mods_disabled_path = '/data/mods-disabled'
                
                # Buscar en mods/ (habilitado)
                result = container.exec_run(f'sh -c "test -f {mods_path}/{mod_name} && echo exists || echo notfound"', user='minecraft')
                output = result.output.decode('utf-8').strip()
                if output == 'exists':
                    container.exec_run(f'rm {mods_path}/{mod_name}', user='minecraft')
                    return JsonResponse({
                        'success': True, 
                        'message': f'Mod {mod_name} deleted'
                    })
                
                # Buscar con .disabled en mods/
                result = container.exec_run(f'sh -c "test -f {mods_path}/{mod_name}.disabled && echo exists || echo notfound"', user='minecraft')
                output = result.output.decode('utf-8').strip()
                if output == 'exists':
                    container.exec_run(f'rm {mods_path}/{mod_name}.disabled', user='minecraft')
                    return JsonResponse({
                        'success': True, 
                        'message': f'Mod {mod_name} deleted'
                    })
                
                # Buscar en mods-disabled/ (deshabilitado)
                result = container.exec_run(f'sh -c "test -f {mods_disabled_path}/{mod_name} && echo exists || echo notfound"', user='minecraft')
                output = result.output.decode('utf-8').strip()
                if output == 'exists':
                    container.exec_run(f'rm {mods_disabled_path}/{mod_name}', user='minecraft')
                    return JsonResponse({
                        'success': True, 
                        'message': f'Mod {mod_name} deleted'
                    })
                
                return JsonResponse({'success': False, 'error': 'Mod not found'}, status=404)
            except Exception as e:
                import traceback
                traceback.print_exc()
                return JsonResponse({'success': False, 'error': f'Error deleting from container: {str(e)}'}, status=500)
        
        # Método original: eliminar del filesystem local
        # Si tenemos file_path completo, usarlo directamente
        if file_path:
            mod_path = file_path if os.path.isabs(file_path) else os.path.join(server.minecraft_data_path, file_path.lstrip('/'))
            if os.path.exists(mod_path):
                os.remove(mod_path)
                return JsonResponse({
                    'success': True, 
                    'message': f'Mod {mod_name} deleted'
                })
        
        # Si no tenemos file_path, buscar en ubicaciones comunes
        mods_path = os.path.join(server.minecraft_data_path, 'mods')
        mods_disabled_path = os.path.join(server.minecraft_data_path, 'mods-disabled')
        
        # Buscar en carpeta mods/
        mod_path = os.path.join(mods_path, mod_name)
        if not os.path.exists(mod_path):
            # Buscar con .disabled
            mod_path = os.path.join(mods_path, f"{mod_name}.disabled")
        
        if not os.path.exists(mod_path):
            # Buscar en carpeta mods-disabled/
            mod_path = os.path.join(mods_disabled_path, mod_name)
        
        if not os.path.exists(mod_path):
            return JsonResponse({'success': False, 'error': 'Mod not found'}, status=404)
        
        # Eliminar archivo
        os.remove(mod_path)
        
        return JsonResponse({
            'success': True, 
            'message': f'Mod {mod_name} deleted'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

