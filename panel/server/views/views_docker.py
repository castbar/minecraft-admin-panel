"""
Vistas para crear y gestionar contenedores Docker desde Django
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
import json
from ..models import Server, UserServerRole
from ..utils.docker_control import (
    create_container_from_compose,
    get_container_status,
    get_container_info,
    create_minecraft_container,
    delete_container,
    _get_docker_client,
    cleanup_containers_blocking_ports,
    find_available_ports_pair,
    find_available_port
)
from ..utils.notifications import send_notification
from ..utils.permissions import _get_server_id_from_request

def _check_server_permission(request, server_id, permission_needed):
    """Helper para verificar permisos"""
    server = get_object_or_404(Server, id=server_id, is_active=True)
    user_role = UserServerRole.objects.filter(user=request.user, server=server).first()
    
    if not user_role:
        return None, JsonResponse({
            'success': False, 
            'error': 'No access to this server'
        }, status=403)
    
    if not user_role.has_permission(permission_needed):
        return None, JsonResponse({
            'success': False, 
            'error': f'Permission denied: {permission_needed} required'
        }, status=403)
    
    return server, None

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def create_server(request):
    """
    Crear un nuevo servidor Minecraft (crea registro en BD y contenedor Docker)
    
    Body JSON:
    {
        "name": "Nuevo Servidor",
        "host": "minecraft-server-2",
        "container_name": "minecraft-server-2",
        "rcon_port": 25575,
        "rcon_password": "password123",
        "minecraft_data_path": "/data"
    }
    """
    # Solo admins pueden crear servidores
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'error': 'Permission denied: Only staff can create servers'
        }, status=403)
    
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        required_fields = ['name', 'host', 'rcon_port', 'rcon_password']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)
        
        # Validar puerto RCON si se proporciona (ahora es opcional, se auto-asignará si no se especifica)
        requested_rcon_port = data.get('rcon_port')
        if requested_rcon_port:
            try:
                rcon_port_val = int(requested_rcon_port)
                if rcon_port_val < 1 or rcon_port_val > 65535:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid RCON port: must be between 1 and 65535'
                    }, status=400)
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid RCON port format'
                }, status=400)
        
            rcon_port = None  # Se auto-asignará más adelante
        
        # Calcular memoria recomendada si no se proporciona
        from ..utils.docker_control import get_recommended_memory
        
        server_type = data.get('server_type', 'vanilla')
        if 'memory_limit_mb' not in data:
            recommended = get_recommended_memory(server_type)
            data['memory_limit_mb'] = recommended['memory_limit_mb']
            data['java_heap_max_mb'] = recommended['java_heap_max_mb']
            data['java_heap_min_mb'] = recommended['java_heap_min_mb']
        
        # Validar que heap_max < memory_limit
        memory_limit_mb = data.get('memory_limit_mb', 2048)
        java_heap_max_mb = data.get('java_heap_max_mb', min(1536, memory_limit_mb - 200))
        java_heap_min_mb = data.get('java_heap_min_mb', 512)
        
        if java_heap_max_mb >= memory_limit_mb:
            java_heap_max_mb = memory_limit_mb - 200
        
        # Obtener nombre del contenedor y puerto
        container_name = data.get('container_name', data['host'])
        
        # Obtener puertos solicitados o auto-asignar si no se especifican
        # El frontend puede enviar null, 0, o no enviar el campo para auto-asignación
        requested_minecraft_port = data.get('port') or data.get('minecraft_port')
        if requested_minecraft_port in [0, None, '0', '']:
            requested_minecraft_port = None
        
        requested_rcon_port = data.get('rcon_port')
        if requested_rcon_port in [0, None, '0', '']:
            requested_rcon_port = None
        
        # Si no se especificó puerto de Minecraft, auto-asignar uno disponible
        if not requested_minecraft_port:
            print("🔍 Auto-asignando puertos disponibles...")
            ports_pair = find_available_ports_pair()
            if not ports_pair.get('minecraft_port') or not ports_pair.get('rcon_port'):
                return JsonResponse({
                    'success': False,
                    'error': 'No se encontraron puertos disponibles. Intenta especificar puertos manualmente.'
                }, status=400)
            minecraft_port = ports_pair['minecraft_port']
            rcon_port = ports_pair['rcon_port']
            print(f"✅ Puertos auto-asignados: Minecraft={minecraft_port}, RCON={rcon_port}")
        else:
            minecraft_port = requested_minecraft_port
            # Si se especificó puerto de Minecraft pero no RCON, buscar uno cerca
            if not requested_rcon_port:
                rcon_port = find_available_port(
                    start_port=minecraft_port + 10,
                    end_port=minecraft_port + 20,
                    exclude_ports=[minecraft_port]
                )
                if not rcon_port:
                    rcon_port = find_available_port(start_port=25575, end_port=26000, exclude_ports=[minecraft_port])
                if not rcon_port:
                    return JsonResponse({
                        'success': False,
                        'error': f'No se encontró un puerto RCON disponible cerca del puerto {minecraft_port}'
                    }, status=400)
                print(f"✅ Puerto RCON auto-asignado: {rcon_port}")
            else:
                rcon_port = requested_rcon_port
        
        # Verificar que los puertos no estén en uso (solo si fueron especificados manualmente)
        if requested_minecraft_port or requested_rcon_port:
            # Limpiar contenedores detenidos que están bloqueando los puertos necesarios
            ports_to_check = [minecraft_port, rcon_port]
            cleanup_result = cleanup_containers_blocking_ports(ports_to_check, exclude_container_name=container_name)
            if cleanup_result.get('removed'):
                print(f"✅ Limpieza automática: {cleanup_result.get('message')}")
                removed_containers = cleanup_result.get('removed', [])
                for removed in removed_containers:
                    print(f"   - Eliminado {removed['name']} (puerto {removed['port']})")
            
            # Verificar si aún hay contenedores corriendo usando estos puertos
            if cleanup_result.get('errors'):
                # Si hay errores porque hay contenedores corriendo, verificar si podemos usar otros puertos
                for error in cleanup_result.get('errors', []):
                    if 'está' in error and 'corriendo' in error:
                        # Intentar auto-asignar puertos alternativos
                        print(f"⚠️ {error}")
                        print("🔍 Intentando encontrar puertos alternativos...")
                        ports_pair = find_available_ports_pair()
                        if ports_pair.get('minecraft_port') and ports_pair.get('rcon_port'):
                            minecraft_port = ports_pair['minecraft_port']
                            rcon_port = ports_pair['rcon_port']
                            print(f"✅ Puertos alternativos asignados: Minecraft={minecraft_port}, RCON={rcon_port}")
                        else:
                            return JsonResponse({
                                'success': False,
                                'error': f'{error}. No se pudieron encontrar puertos alternativos disponibles.'
                            }, status=400)
        
        # rcon_port ya está asignado correctamente arriba (auto-asignado o especificado)
        
        # Crear registro en la base de datos primero
        server = Server.objects.create(
            name=data['name'],
            host=data['host'],
            container_name=data.get('container_name', data['host']),
            port=minecraft_port,
            rcon_port=rcon_port,
            rcon_password=data['rcon_password'],
            minecraft_data_path=data.get('minecraft_data_path', '/data'),
            is_active=True,
            enable_whitelist=data.get('enable_whitelist', True),
            online_mode=data.get('online_mode', False),
            auth_mode=data.get('auth_mode', 'whitelist'),
            is_public=data.get('is_public', False),
            is_hidden=data.get('is_hidden', False),
            # Tipo de servidor y versión
            server_type=server_type,
            minecraft_version=data.get('minecraft_version', 'latest'),
            # Configuración de memoria
            memory_limit_mb=memory_limit_mb,
            java_heap_max_mb=java_heap_max_mb,
            java_heap_min_mb=java_heap_min_mb,
            java_gc_type=data.get('java_gc_type', 'g1'),
            # Mods y plugins base
            install_fabric_api=data.get('install_fabric_api', False),
            install_forge=data.get('install_forge', False),
            install_luckperms=data.get('install_luckperms', False),
            install_worldedit=data.get('install_worldedit', False),
            install_proximity_chat=data.get('install_proximity_chat', False),
            install_spark=data.get('install_spark', True),
            install_more_inventory=data.get('install_more_inventory', False),
            install_jei=data.get('install_jei', False),
            install_wthit=data.get('install_wthit', False),
            install_essentials=data.get('install_essentials', False),
            # Mods y plugins adicionales
            additional_mods=data.get('additional_mods', []),
            additional_plugins=data.get('additional_plugins', []),
            # Puertos adicionales
            additional_ports=data.get('additional_ports', []),
        )
        
        # Asignar rol de admin al usuario que creó el servidor
        UserServerRole.objects.create(
            user=request.user,
            server=server,
            role='admin'
        )
        
        # Crear contenedor Docker automáticamente
        container_result = None
        try:
            # Si hay un contenedor existente con el mismo nombre, eliminarlo primero
            existing_status = get_container_status(container_name)
            if existing_status != 'not_found':
                print(f"⚠️ Contenedor {container_name} ya existe (estado: {existing_status}), eliminándolo...")
                delete_result = delete_container(container_name, force=True)
                if not delete_result.get('success'):
                    print(f"⚠️ No se pudo eliminar el contenedor existente: {delete_result.get('error')}")
                    # Continuar de todas formas, puede que el contenedor se haya eliminado parcialmente
                # Esperar un momento para que Docker libere los puertos
                import time
                time.sleep(2)
            
            container_result = create_minecraft_container(
                container_name=container_name,
                server_type=server_type,
                minecraft_version=data.get('minecraft_version', 'latest'),
                rcon_port=rcon_port,
                rcon_password=data['rcon_password'],
                memory_limit_mb=memory_limit_mb,
                java_heap_max_mb=java_heap_max_mb,
                java_heap_min_mb=java_heap_min_mb,
                minecraft_data_path=data.get('minecraft_data_path', '/data'),
                minecraft_port=minecraft_port,
                network='minecraft-servers',
                start_container=True,
                additional_ports=data.get('additional_ports', [])
            )
            if not container_result.get('success'):
                # Si falla la creación del contenedor, registrar el error pero no fallar la creación del servidor
                print(f"⚠️ Error al crear contenedor para servidor {server.name}: {container_result.get('error')}")
                send_notification(server, 'server_created_with_warning', 
                                f"Servidor '{server.name}' creado pero el contenedor no se pudo crear: {container_result.get('error')}")
            else:
                send_notification(server, 'server_created', f"Servidor '{server.name}' creado correctamente")
        except Exception as e:
            print(f"⚠️ Excepción al crear contenedor: {e}")
            send_notification(server, 'server_created_with_warning', 
                            f"Servidor '{server.name}' creado pero hubo un problema al crear el contenedor: {str(e)}")
        
        # Retornar información completa del servidor creado (mantener server_id para compatibilidad)
        response_data = {
            'success': True,
            'message': f'Servidor {server.name} creado correctamente',
            'server_id': server.id,  # Mantener para compatibilidad
            'data': {
                'id': server.id,
                'name': server.name,
                'host': server.host,
                'container_name': server.container_name,
                'port': server.port,  # Puerto de Minecraft asignado
                'rcon_port': server.rcon_port,  # Puerto RCON asignado
                'minecraft_data_path': server.minecraft_data_path,
                'is_active': server.is_active,
                'is_public': server.is_public,
                'is_hidden': server.is_hidden,
                'auth_mode': server.auth_mode,
                'enable_whitelist': server.enable_whitelist,
                'online_mode': server.online_mode,
                'server_type': server.server_type,
                'minecraft_version': server.minecraft_version,
                'memory_limit_mb': server.memory_limit_mb,
                'java_heap_max_mb': server.java_heap_max_mb,
                'java_heap_min_mb': server.java_heap_min_mb,
                'java_gc_type': server.java_gc_type,
                'role': 'admin',  # El usuario que crea el servidor siempre tiene rol admin
            }
        }
        
        # Agregar información del contenedor si se creó exitosamente
        if container_result and container_result.get('success'):
            response_data['container'] = {
                'created': True,
                'container_id': container_result.get('container_id'),
                'message': container_result.get('message')
            }
            if container_result.get('warning'):
                response_data['container']['warning'] = container_result.get('warning')
        elif container_result and not container_result.get('success'):
            # Si hubo un error al crear el contenedor, agregar información del error
            response_data['container'] = {
                'created': False,
                'error': container_result.get('error', 'Error desconocido')
            }
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["GET"])
def container_info(request, server_id=None):
    """Obtener información detallada del contenedor Docker - Requiere header X-Server-ID"""
    # Obtener server_id del header (método principal) o de la URL (compatibilidad)
    resolved_server_id = _get_server_id_from_request(request) or server_id
    if not resolved_server_id:
        return JsonResponse({
            'success': False, 
            'error': 'Server ID required. Send header X-Server-ID: <id>'
        }, status=400)
    
    server, error_response = _check_server_permission(request, resolved_server_id, 'view')
    if error_response:
        return error_response
    
    container_name = server.container_name or server.host
    info = get_container_info(container_name)
    
    if not info.get('success'):
        # Si el contenedor no existe, devolver información útil en lugar de solo un error
        return JsonResponse({
            'success': False,
            'error': f'Contenedor {container_name} no existe',
            'container_name': container_name,
            'can_create': True,  # Indicar que se puede crear el contenedor
            'server_id': server.id,
            'server_name': server.name
        }, status=404)
    
    return JsonResponse({
        'success': True,
        'data': info
    })

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def create_container_for_server(request, server_id=None):
    """
    Crear contenedor Docker para un servidor existente que no tiene contenedor
    Solo staff o admin del servidor pueden crear contenedores
    """
    # Obtener server_id del header (método principal) o de la URL (compatibilidad)
    resolved_server_id = _get_server_id_from_request(request) or server_id
    if not resolved_server_id:
        return JsonResponse({
            'success': False, 
            'error': 'Server ID required. Send header X-Server-ID: <id>'
        }, status=400)
    
    server = get_object_or_404(Server, id=resolved_server_id, is_active=True)
    
    # Solo staff o admin del servidor pueden crear contenedores
    if not request.user.is_staff:
        user_role = UserServerRole.objects.filter(user=request.user, server=server).first()
        if not user_role or user_role.role != 'admin':
            return JsonResponse({
                'success': False,
                'error': 'Permission denied: Only staff or server admin can create containers'
            }, status=403)
    
    # Verificar si el contenedor ya existe
    container_name = server.container_name or server.host
    status = get_container_status(container_name)
    if status != 'not_found':
        return JsonResponse({
            'success': False,
            'error': f'El contenedor {container_name} ya existe (estado: {status})'
        }, status=400)
    
    try:
        # Obtener puerto de Minecraft del servidor (por defecto 25565)
        minecraft_port = server.port if hasattr(server, 'port') and server.port else 25565
        
        # Crear contenedor Docker
        container_result = create_minecraft_container(
            container_name=container_name,
            server_type=server.server_type,
            minecraft_version=server.minecraft_version,
            rcon_port=server.rcon_port,
            rcon_password=server.rcon_password,
            memory_limit_mb=server.memory_limit_mb,
            java_heap_max_mb=server.java_heap_max_mb,
            java_heap_min_mb=server.java_heap_min_mb,
            minecraft_data_path=server.minecraft_data_path,
            minecraft_port=minecraft_port,
            network='minecraft-servers',
            start_container=True,
            additional_ports=server.additional_ports or []
        )
        
        if container_result.get('success'):
            send_notification(server, 'container_created', f"Contenedor para servidor '{server.name}' creado correctamente")
            return JsonResponse({
                'success': True,
                'message': f'Contenedor {container_name} creado correctamente',
                'container_id': container_result.get('container_id'),
                'data': container_result
            })
        else:
            return JsonResponse({
                'success': False,
                'error': f'Error al crear contenedor: {container_result.get("error")}'
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error: {str(e)}'
        }, status=500)

@csrf_exempt
@login_required
@require_http_methods(["DELETE"])
def delete_server(request, server_id=None):
    """
    Eliminar un servidor (elimina contenedor Docker, marca como inactivo y elimina roles)
    Solo staff o admin del servidor pueden eliminar
    """
    # Obtener server_id del header (método principal) o de la URL (compatibilidad)
    resolved_server_id = _get_server_id_from_request(request) or server_id
    if not resolved_server_id:
        return JsonResponse({
            'success': False, 
            'error': 'Server ID required. Send header X-Server-ID: <id>'
        }, status=400)
    
    server = get_object_or_404(Server, id=resolved_server_id)
    
    # Solo staff o admin del servidor pueden eliminar
    if not request.user.is_staff:
        user_role = UserServerRole.objects.filter(user=request.user, server=server).first()
        if not user_role or user_role.role != 'admin':
            return JsonResponse({
                'success': False,
                'error': 'Permission denied: Only staff or server admin can delete servers'
            }, status=403)
    
    try:
        container_name = server.container_name or server.host
        
        # Eliminar contenedor Docker (si existe)
        container_result = delete_container(container_name, force=True, remove_volumes=False)
        
        # Marcar como inactivo en lugar de eliminar físicamente (soft delete)
        server.is_active = False
        server.save()
        
        # Eliminar todos los roles asociados
        UserServerRole.objects.filter(server=server).delete()
        
        send_notification(server, 'server_deleted', f"Servidor '{server.name}' eliminado")
        
        response_message = f'Servidor {server.name} eliminado correctamente'
        if not container_result.get('success') and container_result.get('status') != 'not_found':
            response_message += f" (advertencia: {container_result.get('error')})"
        
        return JsonResponse({
            'success': True,
            'message': response_message,
            'container_deleted': container_result.get('success', False)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error: {str(e)}'
        }, status=500)

