"""
Vistas simplificadas para configurar mods desde la gestión de mods
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
import json
import os
import configparser
import io
from ..models import Server, UserServerRole
from ..models.models_mods_pool import ModPool
from ..utils.permissions import _get_server_id_from_request

def _validate_config_format(config_content: str, config_format: str) -> str:
    """
    Validar el formato de la configuración según el tipo
    
    Returns:
        str: Mensaje de error si hay error, None si es válido
    """
    if not config_content.strip():
        return None  # Contenido vacío es válido
    
    try:
        if config_format == 'json':
            json.loads(config_content)
        elif config_format == 'yaml' or config_format == 'yml':
            try:
                import yaml
                yaml.safe_load(config_content)
            except ImportError:
                # Si no hay yaml, solo validar sintaxis básica
                pass
            except yaml.YAMLError as e:
                return f'Invalid YAML: {str(e)}'
        elif config_format == 'toml':
            try:
                import tomllib
                tomllib.loads(config_content.encode('utf-8'))
            except ImportError:
                try:
                    import tomli
                    tomli.loads(config_content)
                except ImportError:
                    # Si no hay librería TOML, solo validar sintaxis básica
                    pass
                except Exception as e:
                    return f'Invalid TOML: {str(e)}'
            except Exception as e:
                return f'Invalid TOML: {str(e)}'
        elif config_format == 'properties':
            try:
                config = configparser.ConfigParser()
                config.read_string(config_content)
            except configparser.Error as e:
                return f'Invalid Properties: {str(e)}'
        # 'txt' no necesita validación
    except json.JSONDecodeError as e:
        return f'Invalid JSON: {str(e)}'
    except Exception as e:
        return f'Validation error: {str(e)}'
    
    return None  # Válido

@login_required
@require_http_methods(["GET"])
def mod_config_get(request, server_id=None):
    """
    Obtener configuración de un mod - Requiere header X-Server-ID
    
    Query params:
    - mod_name: nombre del archivo del mod (ej: 'cobblemon.jar')
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
    
    mod_name = request.GET.get('mod_name', '').strip()
    if not mod_name:
        return JsonResponse({'success': False, 'error': 'mod_name parameter required'}, status=400)
    
    # Limpiar nombre (remover .jar, .disabled, etc.)
    clean_name = mod_name.replace('.jar', '').replace('.disabled', '').strip()
    
    # Buscar en pool de mods
    mod_pool = ModPool.objects.filter(name__iexact=clean_name).first()
    
    # Si el mod está en el pool y tiene configuración, usar esa
    if mod_pool and mod_pool.config_file_path:
        config_file_path = os.path.join(server.minecraft_data_path, mod_pool.config_file_path)
        config_format = mod_pool.config_format
        default_config = mod_pool.default_config or ''
        mod_display_name = mod_pool.display_name
    else:
        # Si no está en el pool, usar ruta por defecto basada en el nombre del mod
        # Buscar archivos de configuración comunes en el contenedor
        if server.container_name:
            import docker
            try:
                client = docker.from_env()
                container = client.containers.get(server.container_name)
                
                # Rutas comunes de configuración
                possible_paths = [
                    f'/data/config/{clean_name}.json',
                    f'/data/config/{clean_name}.toml',
                    f'/data/config/{clean_name}.properties',
                    f'/data/config/{clean_name}.yml',
                    f'/data/config/{clean_name}.yaml',
                ]
                
                config_file_path = None
                config_format = 'json'
                
                for path in possible_paths:
                    result = container.exec_run(f'test -f {path} && echo "exists" || echo ""', user='minecraft')
                    if result.output.decode('utf-8').strip() == 'exists':
                        config_file_path = path
                        if path.endswith('.toml'):
                            config_format = 'toml'
                        elif path.endswith('.properties'):
                            config_format = 'properties'
                        elif path.endswith('.yml') or path.endswith('.yaml'):
                            config_format = 'yaml'
                        break
                
                if not config_file_path:
                    # Crear ruta por defecto
                    config_file_path = f'/data/config/{clean_name}.json'
                    config_format = 'json'
                
                # Leer contenido si existe
                result = container.exec_run(f'cat {config_file_path} 2>/dev/null || echo ""', user='minecraft')
                default_config = result.output.decode('utf-8').strip()
                mod_display_name = clean_name
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Error accessing container: {str(e)}'
                }, status=500)
        else:
            # Sin contenedor, usar filesystem local
            config_file_path = os.path.join(server.minecraft_data_path, 'config', f'{clean_name}.json')
            config_format = 'json'
            default_config = ''
            mod_display_name = clean_name
    
    # Leer configuración actual si existe
    config_content = default_config
    file_exists = False
    
    if server.container_name:
        import docker
        try:
            client = docker.from_env()
            container = client.containers.get(server.container_name)
            result = container.exec_run(f'test -f {config_file_path} && cat {config_file_path} || echo ""', user='minecraft')
            content = result.output.decode('utf-8').strip()
            if content:
                file_exists = True
                config_content = content
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error reading config from container: {str(e)}'
            }, status=500)
    else:
        if os.path.exists(config_file_path):
            file_exists = True
            try:
                with open(config_file_path, 'r', encoding='utf-8') as f:
                    config_content = f.read()
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Error reading config file: {str(e)}'
                }, status=500)
    
    return JsonResponse({
        'success': True,
        'data': {
            'mod_name': mod_name,
            'mod_pool': {
                'id': mod_pool.id if mod_pool else None,
                'display_name': mod_display_name,
                'mod_type': mod_pool.mod_type if mod_pool else 'mod',
            } if mod_pool else None,
            'config_file_path': config_file_path.replace(server.minecraft_data_path, '').lstrip('/') if not server.container_name else config_file_path.replace('/data/', ''),
            'config_format': config_format,
            'config_content': config_content,
            'file_exists': file_exists,
            'is_default': config_content == default_config if default_config else False,
        }
    })

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def mod_config_update(request, server_id=None):
    """
    Actualizar configuración de un mod - Requiere header X-Server-ID
    
    Body JSON:
    {
        "mod_name": "cobblemon.jar",
        "config_content": "{...}"
    }
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
        config_content = data.get('config_content', '').strip()
        
        if not mod_name:
            return JsonResponse({'success': False, 'error': 'mod_name is required'}, status=400)
        
        if not config_content:
            return JsonResponse({'success': False, 'error': 'config_content is required'}, status=400)
        
        # Limpiar nombre
        clean_name = mod_name.replace('.jar', '').replace('.disabled', '').strip()
        
        # Buscar en pool de mods
        mod_pool = ModPool.objects.filter(name__iexact=clean_name).first()
        
        # Determinar formato y ruta
        config_format = 'json'
        config_file_path = None
        
        if mod_pool and mod_pool.config_file_path:
            # Usar información del pool
            config_file_path = os.path.join(server.minecraft_data_path, mod_pool.config_file_path)
            config_format = mod_pool.config_format
        else:
            # Si no está en el pool, intentar construir ruta por defecto
            # Permitir configurar mods aunque no estén en el pool
            # Usar ruta por defecto basada en el nombre
            if server.container_name:
                import docker
                try:
                    client = docker.from_env()
                    container = client.containers.get(server.container_name)
                    
                    # Rutas comunes de configuración
                    possible_paths = [
                        f'/data/config/{clean_name}.json',
                        f'/data/config/{clean_name}.toml',
                        f'/data/config/{clean_name}.properties',
                        f'/data/config/{clean_name}.yml',
                        f'/data/config/{clean_name}.yaml',
                    ]
                    
                    config_file_path = None
                    config_format = 'json'
                    
                    for path in possible_paths:
                        result = container.exec_run(f'test -f {path} && echo "exists" || echo ""', user='minecraft')
                        if result.output.decode('utf-8').strip() == 'exists':
                            config_file_path = path
                            if path.endswith('.toml'):
                                config_format = 'toml'
                            elif path.endswith('.properties'):
                                config_format = 'properties'
                            elif path.endswith('.yml') or path.endswith('.yaml'):
                                config_format = 'yaml'
                            break
                    
                    if not config_file_path:
                        # Crear ruta por defecto
                        config_file_path = f'/data/config/{clean_name}.json'
                        config_format = 'json'
                    
                    # Leer contenido si existe
                    result = container.exec_run(f'cat {config_file_path} 2>/dev/null || echo ""', user='minecraft')
                    default_config = result.output.decode('utf-8').strip()
                    
                    # Escribir archivo
                    result = container.exec_run(f'mkdir -p /data/config && touch {config_file_path}', user='minecraft')
                    result = container.exec_run(f'chown minecraft:minecraft {config_file_path}', user='root')
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Configuration for {clean_name} updated',
                        'data': {
                            'mod_name': mod_name,
                            'config_file_path': config_file_path.replace('/data/', ''),
                            'file_exists': bool(default_config),
                        }
                    })
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'error': f'Error accessing container: {str(e)}'
                    }, status=500)
            
            # Si no está en el pool y no hay contenedor, devolver error
            return JsonResponse({
                'success': False,
                'error': 'Mod not found in pool or has no configuration'
            }, status=404)
        
        # Validar formato según el tipo
        validation_error = _validate_config_format(config_content, mod_pool.config_format)
        if validation_error:
            return JsonResponse({
                'success': False,
                'error': validation_error
            }, status=400)
        
        # Construir ruta del archivo
        if server.container_name:
            # Si el servidor tiene contenedor, escribir en el contenedor
            import docker
            try:
                client = docker.from_env()
                container = client.containers.get(server.container_name)
                
                # Construir ruta completa en el contenedor
                if mod_pool.config_file_path.startswith('/'):
                    config_file_path = mod_pool.config_file_path
                else:
                    config_file_path = f'/data/{mod_pool.config_file_path}'
                
                # Validar formato antes de escribir
                validation_error = _validate_config_format(config_content, mod_pool.config_format)
                if validation_error:
                    return JsonResponse({
                        'success': False,
                        'error': validation_error
                    }, status=400)
                
                # Copiar archivo al contenedor
                import tarfile
                import io
                import tempfile
                
                with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as tmp_file:
                    tmp_file.write(config_content)
                    tmp_path = tmp_file.name
                
                try:
                    with open(tmp_path, 'rb') as f:
                        file_content = f.read()
                    
                    tar_stream = io.BytesIO()
                    with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                        tarinfo = tarfile.TarInfo(name=os.path.basename(config_file_path))
                        tarinfo.size = len(file_content)
                        tar.addfile(tarinfo, io.BytesIO(file_content))
                    
                    tar_stream.seek(0)
                    container.put_archive(os.path.dirname(config_file_path), tar_stream.read())
                    
                    # Asegurar permisos
                    container.exec_run(f'chown minecraft:minecraft {config_file_path}', user='root')
                finally:
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Error writing to container: {str(e)}'
                }, status=500)
        else:
            # Sin contenedor, usar filesystem local
            config_file_path = os.path.join(server.minecraft_data_path, mod_pool.config_file_path)
            
            # Validar formato antes de escribir
            validation_error = _validate_config_format(config_content, mod_pool.config_format)
            if validation_error:
                return JsonResponse({
                    'success': False,
                    'error': validation_error
                }, status=400)
            
            # Crear directorio si no existe
            config_dir = os.path.dirname(config_file_path)
            os.makedirs(config_dir, exist_ok=True)
            
            # Escribir archivo
            with open(config_file_path, 'w', encoding='utf-8') as f:
                f.write(config_content)
        
        return JsonResponse({
            'success': True,
            'message': f'Configuration for {mod_pool.display_name} updated',
            'data': {
                'mod_name': mod_name,
                'config_file_path': mod_pool.config_file_path,
                'file_exists': True,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def mod_config_reset(request, server_id=None):
    """
    Resetear configuración de un mod a los valores por defecto - Requiere header X-Server-ID
    
    Body JSON:
    {
        "mod_name": "cobblemon.jar"
    }
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
            return JsonResponse({'success': False, 'error': 'mod_name is required'}, status=400)
        
        # Limpiar nombre
        clean_name = mod_name.replace('.jar', '').replace('.disabled', '').strip()
        
        # Buscar en pool de mods
        mod_pool = ModPool.objects.filter(name__iexact=clean_name).first()
        
        if not mod_pool or not mod_pool.config_file_path or not mod_pool.default_config:
            return JsonResponse({
                'success': False,
                'error': 'Mod not found in pool or has no default configuration'
            }, status=404)
        
        # Construir ruta del archivo
        config_file_path = os.path.join(server.minecraft_data_path, mod_pool.config_file_path)
        
        # Crear directorio si no existe
        config_dir = os.path.dirname(config_file_path)
        os.makedirs(config_dir, exist_ok=True)
        
        # Escribir configuración por defecto
        with open(config_file_path, 'w', encoding='utf-8') as f:
            f.write(mod_pool.default_config)
        
        return JsonResponse({
            'success': True,
            'message': f'Configuration for {mod_pool.display_name} reset to default',
            'data': {
                'mod_name': mod_name,
                'config_file_path': mod_pool.config_file_path,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def config_files_list(request, server_id=None):
    """
    Lista archivos y directorios en una ruta específica dentro del contenedor del servidor.
    
    Query params:
    - path: Ruta a explorar (ej: '/data/config', '/data/config/voicechat')
    """
    resolved_server_id = _get_server_id_from_request(request) or server_id
    if not resolved_server_id:
        return JsonResponse({'success': False, 'error': 'Server ID required'}, status=400)
    
    try:
        server = get_object_or_404(Server, id=resolved_server_id, is_active=True)
    except Server.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Server not found'}, status=404)
    
    user_role = UserServerRole.objects.filter(user=request.user, server=server).first()
    if not user_role or not user_role.has_permission('manage_mods'):
        return JsonResponse({'success': False, 'error': 'Permission denied: manage_mods required'}, status=403)
    
    target_path = request.GET.get('path', '/data/config').strip()
    if not target_path.startswith('/data/'):
        return JsonResponse({'success': False, 'error': 'Invalid path. Must be within /data/'}, status=400)
    
    if server.container_name:
        import docker
        try:
            client = docker.from_env()
            container = client.containers.get(server.container_name)
            
            # Listar contenido del directorio
            result = container.exec_run(f'ls -la {target_path}', user='minecraft')
            if result.exit_code != 0:
                return JsonResponse({'success': False, 'error': f'Error listing directory: {result.output.decode("utf-8")}'}, status=500)
            
            output_lines = result.output.decode('utf-8').splitlines()
            files_info = []
            
            for line in output_lines:
                if line.startswith('total') or not line.strip():
                    continue
                
                # Parsear línea de ls -la
                # Formato: permissions links owner group size date time name
                # Ejemplo: drwxr-xr-x 2 minecraft minecraft 4096 Jan 11 15:00 voicechat
                parts = line.split(None, 8)  # Dividir en máximo 9 partes para manejar espacios en nombres
                if len(parts) < 9:
                    continue
                
                permissions = parts[0]
                try:
                    size = int(parts[4])
                except (ValueError, IndexError):
                    size = 0
                name = parts[8]  # El nombre puede tener espacios, así que tomamos todo lo que queda
                
                if name in ['.', '..']:
                    continue
                
                is_dir = permissions.startswith('d')
                
                files_info.append({
                    'name': name,
                    'is_dir': is_dir,
                    'size': size if not is_dir else 0,
                    'path': os.path.join(target_path, name).replace('\\', '/')
                })
            
            return JsonResponse({'success': True, 'data': files_info})
        except docker.errors.NotFound:
            return JsonResponse({'success': False, 'error': f'Container {server.container_name} not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error accessing container: {str(e)}'}, status=500)
    else:
        # Fallback para filesystem local (si no hay contenedor)
        full_path = os.path.join(server.minecraft_data_path, target_path.replace('/data/', ''))
        if not os.path.exists(full_path):
            return JsonResponse({'success': False, 'error': 'Path not found on local filesystem'}, status=404)
        
        files_info = []
        for name in os.listdir(full_path):
            item_path = os.path.join(full_path, name)
            is_dir = os.path.isdir(item_path)
            size = os.path.getsize(item_path) if not is_dir else 0
            files_info.append({
                'name': name,
                'is_dir': is_dir,
                'size': size,
                'path': os.path.join(target_path, name).replace('\\', '/')
            })
        return JsonResponse({'success': True, 'data': files_info})

@login_required
@require_http_methods(["GET"])
def config_file_read(request, server_id=None):
    """
    Lee el contenido de un archivo específico dentro del contenedor del servidor.
    
    Query params:
    - file_path: Ruta completa del archivo (ej: '/data/config/voicechat/voicechat-server.properties')
    """
    resolved_server_id = _get_server_id_from_request(request) or server_id
    if not resolved_server_id:
        return JsonResponse({'success': False, 'error': 'Server ID required'}, status=400)
    
    try:
        server = get_object_or_404(Server, id=resolved_server_id, is_active=True)
    except Server.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Server not found'}, status=404)
    
    user_role = UserServerRole.objects.filter(user=request.user, server=server).first()
    if not user_role or not user_role.has_permission('manage_mods'):
        return JsonResponse({'success': False, 'error': 'Permission denied: manage_mods required'}, status=403)
    
    file_path = request.GET.get('file_path', '').strip()
    if not file_path or not file_path.startswith('/data/'):
        return JsonResponse({'success': False, 'error': 'Invalid file path. Must be within /data/'}, status=400)
    
    if server.container_name:
        import docker
        try:
            client = docker.from_env()
            container = client.containers.get(server.container_name)
            
            # Verificar si es un directorio antes de intentar leerlo (usar comillas para manejar espacios)
            result = container.exec_run(f'sh -c \'test -d "{file_path}" && echo "dir" || echo "file"\'', user='minecraft')
            is_directory = result.output.decode('utf-8').strip() == 'dir'
            
            if is_directory:
                return JsonResponse({
                    'success': False, 
                    'error': f'{file_path} is a directory. Please specify a file path.',
                    'is_directory': True
                }, status=400)
            
            # Verificar que el archivo existe (usar comillas para manejar espacios en nombres)
            # Primero verificar con root para ver si existe, luego intentar leer con minecraft
            result_check = container.exec_run(f'sh -c \'test -f "{file_path}" && echo "exists" || echo ""\'', user='root')
            if result_check.output.decode('utf-8').strip() != 'exists':
                return JsonResponse({
                    'success': False, 
                    'error': f'File {file_path} does not exist'
                }, status=404)
            
            # Intentar leer con minecraft primero, si falla intentar con root
            result = container.exec_run(f'sh -c \'cat "{file_path}"\'', user='minecraft')
            if result.exit_code != 0:
                # Si falla con minecraft, intentar con root
                result = container.exec_run(f'sh -c \'cat "{file_path}"\'', user='root')
                # Si aún así falla, devolver error
                if result.exit_code != 0:
                    return JsonResponse({
                        'success': False, 
                        'error': f'Error reading file: {result.output.decode("utf-8").strip()}'
                    }, status=500)
            
            if result.exit_code == 0:
                content = result.output.decode('utf-8')
                # Determinar formato basado en extensión
                format_type = 'txt'
                if file_path.endswith('.json'):
                    format_type = 'json'
                elif file_path.endswith('.toml'):
                    format_type = 'toml'
                elif file_path.endswith('.properties'):
                    format_type = 'properties'
                elif file_path.endswith('.yml') or file_path.endswith('.yaml'):
                    format_type = 'yaml'
                
                return JsonResponse({'success': True, 'data': {'content': content, 'path': file_path, 'format': format_type}})
            else:
                error_msg = result.output.decode('utf-8').strip()
                return JsonResponse({'success': False, 'error': f'Error reading file: {error_msg}'}, status=500)
        except docker.errors.NotFound:
            return JsonResponse({'success': False, 'error': f'Container {server.container_name} not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error accessing container: {str(e)}'}, status=500)
    else:
        # Fallback para filesystem local
        full_path = os.path.join(server.minecraft_data_path, file_path.replace('/data/', ''))
        if not os.path.exists(full_path):
            return JsonResponse({'success': False, 'error': 'File not found on local filesystem'}, status=404)
        
        # Verificar si es un directorio
        if os.path.isdir(full_path):
            return JsonResponse({
                'success': False, 
                'error': f'{file_path} is a directory. Please specify a file path.',
                'is_directory': True
            }, status=400)
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Determinar formato basado en extensión
        format_type = 'txt'
        if file_path.endswith('.json'):
            format_type = 'json'
        elif file_path.endswith('.toml'):
            format_type = 'toml'
        elif file_path.endswith('.properties'):
            format_type = 'properties'
        elif file_path.endswith('.yml') or file_path.endswith('.yaml'):
            format_type = 'yaml'
        
        return JsonResponse({'success': True, 'data': {'content': content, 'path': file_path, 'format': format_type}})

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def config_file_write(request, server_id=None):
    """
    Escribe contenido en un archivo específico dentro del contenedor del servidor.
    
    Body JSON:
    {
        "path": "/data/config/voicechat/voicechat-server.properties",
        "content": "new_content_here",
        "format": "properties" # Opcional, para validación
    }
    """
    resolved_server_id = _get_server_id_from_request(request) or server_id
    if not resolved_server_id:
        return JsonResponse({'success': False, 'error': 'Server ID required'}, status=400)
    
    try:
        server = get_object_or_404(Server, id=resolved_server_id, is_active=True)
    except Server.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Server not found'}, status=404)
    
    user_role = UserServerRole.objects.filter(user=request.user, server=server).first()
    if not user_role or not user_role.has_permission('manage_mods'):
        return JsonResponse({'success': False, 'error': 'Permission denied: manage_mods required'}, status=403)
    
    try:
        data = json.loads(request.body)
        # Aceptar tanto 'path' como 'file_path' para compatibilidad
        file_path = data.get('path', data.get('file_path', '')).strip()
        content = data.get('content', '')
        config_format = data.get('format', 'txt') # Default a txt si no se especifica
        
        if not file_path or not file_path.startswith('/data/'):
            return JsonResponse({'success': False, 'error': 'Invalid file path. Must be within /data/'}, status=400)
        
        # Validar formato si se especifica
        validation_error = _validate_config_format(content, config_format)
        if validation_error:
            return JsonResponse({'success': False, 'error': validation_error}, status=400)
        
        if server.container_name:
            import docker
            import tarfile
            
            try:
                client = docker.from_env()
                container = client.containers.get(server.container_name)
                
                # Crear un archivo temporal en memoria y copiarlo al contenedor
                tar_stream = io.BytesIO()
                dir_path = os.path.dirname(file_path)
                file_name = os.path.basename(file_path)
                
                with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                    tarinfo = tarfile.TarInfo(name=file_name)
                    tarinfo.size = len(content.encode('utf-8'))
                    tar.addfile(tarinfo, io.BytesIO(content.encode('utf-8')))
                
                tar_stream.seek(0)
                
                # Copiar archivo al contenedor del servidor usando put_archive
                container.put_archive(dir_path, tar_stream.read())
                
                # Asegurar permisos correctos (usar comillas para manejar espacios)
                container.exec_run(f'chown minecraft:minecraft "{file_path}"', user='root')
                
                return JsonResponse({'success': True, 'message': f'File {file_path} updated successfully'})
            except docker.errors.NotFound:
                return JsonResponse({'success': False, 'error': f'Container {server.container_name} not found'}, status=404)
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Error writing to container: {str(e)}'}, status=500)
        else:
            # Fallback para filesystem local
            full_path = os.path.join(server.minecraft_data_path, file_path.replace('/data/', ''))
            
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return JsonResponse({'success': True, 'message': f'File {file_path} updated successfully'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON in request body'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)