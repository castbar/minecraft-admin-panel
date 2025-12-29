from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
import json
import os
import mcrcon
from ..models import Server, UserServerRole
from ..utils.notifications import send_notification
from ..utils.docker_control import (
    start_container, stop_container, restart_container,
    pause_container, unpause_container, get_container_status,
    create_container_from_compose, get_container_info
)
from ..utils.permissions import _get_server_id_from_request
from django.utils import timezone
from datetime import timedelta
import docker

def _get_rcon_connection(server):
    """Conectar a RCON para un servidor específico"""
    try:
        # Log para debugging
        print(f"🔌 Intentando conectar RCON: host={server.host}, port={server.rcon_port}")
        
        # Si el host es un nombre de contenedor Docker, usar ese nombre directamente
        # Si es una IP, usar la IP
        host = server.host
        
        rcon = mcrcon.MCRcon(host, server.rcon_password, port=server.rcon_port)
        rcon.connect()
        print(f"✅ RCON conectado exitosamente a {server.name} (host: {host})")
        return rcon
    except Exception as e:
        print(f"❌ RCON Error for {server.name}: {str(e)}")
        print(f"   Host: {server.host}, Port: {server.rcon_port}, Password: {'*' * len(server.rcon_password) if server.rcon_password else 'None'}")
        import traceback
        traceback.print_exc()
        return None

@login_required
@require_http_methods(["GET"])
def servers_list(request):
    """Listar servidores disponibles para el usuario"""
    from ..models.models_multi import ServerSession
    
    # Detectar si el cliente está en la misma red/VPN
    client_ip = _get_client_ip(request)
    is_local_network = _is_local_network(client_ip)
    
    user_servers = UserServerRole.objects.filter(user=request.user).select_related('server')
    servers = []
    for user_role in user_servers:
        if user_role.server.is_active:
            # Si el servidor está oculto, solo mostrarlo si está en la misma red
            if user_role.server.is_hidden and not is_local_network:
                continue
            
            # Obtener información de sesión guardada
            session = ServerSession.objects.filter(
                user=request.user,
                server=user_role.server
            ).first()
            
            servers.append({
                'id': user_role.server.id,
                'name': user_role.server.name,
                'host': user_role.server.host,
                'role': user_role.role,
                'is_hidden': user_role.server.is_hidden,
                'last_accessed': session.last_accessed.isoformat() if session else None,
                'is_favorite': session.is_favorite if session else False,
            })
    
    # Ordenar por último acceso o favoritos
    servers.sort(key=lambda x: (
        not x.get('is_favorite', False),
        x.get('last_accessed') is None,
        x.get('last_accessed', '')
    ), reverse=True)
    
    return JsonResponse({'success': True, 'data': servers})

def _get_client_ip(request):
    """Obtener IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def _is_local_network(ip):
    """Verificar si la IP está en la red local/VPN"""
    import ipaddress
    
    # Rangos de red local
    local_ranges = [
        ipaddress.IPv4Network('10.0.0.0/8'),
        ipaddress.IPv4Network('172.16.0.0/12'),
        ipaddress.IPv4Network('192.168.0.0/16'),
        ipaddress.IPv4Network('100.0.0.0/8'),  # Tailscale
    ]
    
    try:
        ip_obj = ipaddress.IPv4Address(ip)
        for network in local_ranges:
            if ip_obj in network:
                return True
    except:
        pass
    
    return False

@login_required
@require_http_methods(["GET"])
def server_status(request, server_id=None):
    """Obtener estado del servidor - Requiere header X-Server-ID"""
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
    
    # Obtener estado del contenedor Docker
    container_status = get_container_status(server.container_name) if server.container_name else None
    
    # Intentar conectar vía RCON para verificar estado de Minecraft
    rcon = _get_rcon_connection(server)
    is_online = rcon is not None
    
    players = []
    player_count = 0
    max_players = 20
    
    if rcon:
        try:
            response = rcon.command('list')
            # Parsear jugadores
            if 'online:' in response:
                players_str = response.split('online:')[1].strip()
                if players_str:
                    players = [p.strip() for p in players_str.split(',') if p.strip()]
                    player_count = len(players)
            
            # Obtener max players
            if 'of a max of' in response:
                try:
                    max_players = int(response.split('of a max of')[1].split()[0])
                except:
                    pass
        except Exception as e:
            send_notification(server, 'rcon_error', f"Error al obtener lista de jugadores: {e}")
        finally:
            if rcon:
                try:
                    rcon.disconnect()
                except:
                    pass
    
    # Obtener estadísticas del contenedor si está disponible
    cpu_usage = None
    memory_usage = None
    memory_max = None
    
    if server.container_name and container_status:
        try:
            client = docker.from_env()
            container = client.containers.get(server.container_name)
            stats = container.stats(stream=False)
            
            # Calcular CPU
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
            if system_delta > 0:
                cpu_usage = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100
            
            # Calcular memoria
            memory_usage = stats['memory_stats'].get('usage', 0)
            memory_max = stats['memory_stats'].get('limit', 0)
        except Exception as e:
            print(f"Error obteniendo stats del contenedor: {e}")
    
    return JsonResponse({
        'success': True,
        'data': {
            'online': is_online,
            'players': players,
            'player_count': player_count,
            'max_players': max_players,
            'container_status': container_status,
            'cpu_usage': round(cpu_usage, 2) if cpu_usage else None,
            'memory_usage': memory_usage,
            'memory_max': memory_max,
            'memory_usage_mb': round(memory_usage / (1024 * 1024), 2) if memory_usage else None,
            'memory_max_mb': round(memory_max / (1024 * 1024), 2) if memory_max else None,
        }
    })

@login_required
@require_http_methods(["GET"])
def server_stats(request, server_id=None):
    """Obtener estadísticas históricas del servidor para gráficos - Requiere header X-Server-ID"""
    from ..models.models_stats import ServerStatistic
    
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
    
    # Obtener estadísticas de las últimas 24 horas
    since = timezone.now() - timedelta(hours=24)
    stats = ServerStatistic.objects.filter(
        server=server,
        timestamp__gte=since
    ).order_by('timestamp')
    
    # Preparar datos para gráficos
    timestamps = [s.timestamp.isoformat() for s in stats]
    players_data = [s.players_online for s in stats]
    cpu_data = [s.cpu_usage if s.cpu_usage else 0 for s in stats]
    memory_data = [round(s.memory_usage / (1024 * 1024), 2) if s.memory_usage else 0 for s in stats]
    tps_data = [s.tps if s.tps else 20 for s in stats]
    
    return JsonResponse({
        'success': True,
        'data': {
            'timestamps': timestamps,
            'players': players_data,
            'cpu': cpu_data,
            'memory': memory_data,
            'tps': tps_data,
        }
    })

def _check_server_permission(request, server_id, permission_needed):
    server = get_object_or_404(Server, id=server_id, is_active=True)
    user_role = UserServerRole.objects.filter(user=request.user, server=server).first()
    
    if not user_role:
        return None, JsonResponse({'success': False, 'error': 'No access to this server'}, status=403)
    
    if not user_role.has_permission(permission_needed):
        return None, JsonResponse({'success': False, 'error': f'Permission denied: {permission_needed} required'}, status=403)
    
    return server, None

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def server_control(request, server_id=None, action=None):
    """Controlar servidor: start, stop, restart, pause, unpause - Requiere header X-Server-ID"""
    # Obtener server_id del header (método principal) o de la URL (compatibilidad)
    resolved_server_id = _get_server_id_from_request(request) or server_id
    if not resolved_server_id:
        return JsonResponse({
            'success': False, 
            'error': 'Server ID required. Send header X-Server-ID: <id>'
        }, status=400)
    
    # Obtener action de la URL o del body
    if not action:
        try:
            data = json.loads(request.body)
            action = data.get('action')
        except (json.JSONDecodeError, AttributeError):
            pass
    
    if not action:
        return JsonResponse({
            'success': False, 
            'error': 'Action required (start, stop, restart, pause, unpause)'
        }, status=400)
    
    server, error_response = _check_server_permission(request, resolved_server_id, 'control_server')
    if error_response:
        return error_response
    
    if not server.container_name:
        return JsonResponse({'success': False, 'error': 'Server is not configured with a Docker container name for control.'}, status=400)

    valid_actions = ['start', 'stop', 'restart', 'pause', 'unpause']
    if action not in valid_actions:
        return JsonResponse({'success': False, 'error': f'Invalid action. Valid: {valid_actions}'}, status=400)
    
    try:
        if action == 'start':
            start_container(server.container_name)
        elif action == 'stop':
            stop_container(server.container_name)
        elif action == 'restart':
            restart_container(server.container_name)
        elif action == 'pause':
            pause_container(server.container_name)
        elif action == 'unpause':
            unpause_container(server.container_name)
        
        send_notification(server, 'server_control', f"Comando '{action}' enviado al servidor '{server.name}'.")
        return JsonResponse({
            'success': True,
            'message': f'Server {action} command sent to container {server.container_name}'
        })
    except Exception as e:
        send_notification(server, 'server_control_failed', f"Fallo el comando '{action}' para '{server.name}': {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def whitelist_add(request, server_id=None):
    """Agregar usuario a whitelist - Requiere header X-Server-ID"""
    from django.shortcuts import get_object_or_404
    
    # Obtener server_id del header (método principal) o de la URL (compatibilidad)
    resolved_server_id = _get_server_id_from_request(request) or server_id
    if not resolved_server_id:
        return JsonResponse({
            'success': False, 
            'error': 'Server ID required. Send header X-Server-ID: <id>'
        }, status=400)
    
    # Obtener servidor y verificar permisos
    try:
        server = get_object_or_404(Server, id=resolved_server_id, is_active=True)
    except:
        return JsonResponse({'success': False, 'error': 'Server not found'}, status=404)
    
    user_role = UserServerRole.objects.filter(
        user=request.user,
        server=server
    ).first()
    
    if not user_role:
        return JsonResponse({'success': False, 'error': 'No access to this server'}, status=403)
    
    if not user_role.has_permission('manage_whitelist'):
        return JsonResponse({'success': False, 'error': 'Permission denied: manage_whitelist required'}, status=403)
    
    data = json.loads(request.body)
    username = data.get('username', '').strip()
    
    if not username:
        return JsonResponse({'success': False, 'error': 'Username required'}, status=400)
    
    rcon = _get_rcon_connection(server)
    if rcon is None:
        return JsonResponse({
            'success': False, 
            'error': f'Cannot connect to RCON. Host: {server.host}, Port: {server.rcon_port}'
        }, status=500)
    
    try:
        response = rcon.command(f'whitelist add {username}')
        send_notification(server, 'whitelist_change', f"Usuario '{username}' agregado a whitelist.")
        return JsonResponse({'success': True, 'message': f'User {username} added', 'response': response})
    except Exception as e:
        send_notification(server, 'rcon_error', f"Error al agregar {username} a whitelist: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    finally:
        try:
            rcon.disconnect()
        except:
            pass

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def whitelist_remove(request, server_id=None):
    """Eliminar usuario de whitelist - Requiere header X-Server-ID"""
    from django.shortcuts import get_object_or_404
    
    # Obtener server_id del header (método principal) o de la URL (compatibilidad)
    resolved_server_id = _get_server_id_from_request(request) or server_id
    if not resolved_server_id:
        return JsonResponse({
            'success': False, 
            'error': 'Server ID required. Send header X-Server-ID: <id>'
        }, status=400)
    
    # Obtener servidor y verificar permisos
    try:
        server = get_object_or_404(Server, id=resolved_server_id, is_active=True)
    except:
        return JsonResponse({'success': False, 'error': 'Server not found'}, status=404)
    
    user_role = UserServerRole.objects.filter(
        user=request.user,
        server=server
    ).first()
    
    if not user_role:
        return JsonResponse({'success': False, 'error': 'No access to this server'}, status=403)
    
    if not user_role.has_permission('manage_whitelist'):
        return JsonResponse({'success': False, 'error': 'Permission denied: manage_whitelist required'}, status=403)
    
    data = json.loads(request.body)
    username = data.get('username', '').strip()
    
    if not username:
        return JsonResponse({'success': False, 'error': 'Username required'}, status=400)
    
    rcon = _get_rcon_connection(server)
    if rcon is None:
        return JsonResponse({
            'success': False, 
            'error': f'Cannot connect to RCON. Host: {server.host}, Port: {server.rcon_port}'
        }, status=500)
    
    try:
        response = rcon.command(f'whitelist remove {username}')
        send_notification(server, 'whitelist_change', f"Usuario '{username}' eliminado de whitelist.")
        return JsonResponse({'success': True, 'message': f'User {username} removed', 'response': response})
    except Exception as e:
        send_notification(server, 'rcon_error', f"Error al eliminar {username} de whitelist: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    finally:
        try:
            rcon.disconnect()
        except:
            pass

@login_required
@require_http_methods(["GET"])
def whitelist_list(request, server_id=None):
    """Listar usuarios en whitelist - Requiere header X-Server-ID"""
    from django.shortcuts import get_object_or_404
    
    # Obtener server_id del header (método principal) o de la URL (compatibilidad)
    resolved_server_id = _get_server_id_from_request(request) or server_id
    if not resolved_server_id:
        return JsonResponse({
            'success': False, 
            'error': 'Server ID required. Send header X-Server-ID: <id>'
        }, status=400)
    
    # Obtener servidor y verificar permisos
    server = get_object_or_404(Server, id=resolved_server_id, is_active=True)
    user_role = UserServerRole.objects.filter(
        user=request.user,
        server=server
    ).first()
    
    if not user_role:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    # Intentar obtener whitelist vía RCON primero (más confiable)
    rcon = _get_rcon_connection(server)
    if rcon:
        try:
            response = rcon.command('whitelist list')
            # Parsear respuesta: "There are X whitelisted players: player1, player2"
            players = []
            if ': ' in response:
                players_str = response.split(': ')[1].strip()
                if players_str and players_str != '':
                    players = [p.strip() for p in players_str.split(',') if p.strip()]
            
            # Convertir a formato esperado por el frontend
            whitelist_data = [{'name': p, 'uuid': ''} for p in players]
            return JsonResponse({'success': True, 'data': whitelist_data})
        except Exception as e:
            print(f"Error obteniendo whitelist vía RCON: {e}")
            import traceback
            traceback.print_exc()
        finally:
            try:
                rcon.disconnect()
            except:
                pass
    
    # Fallback: leer archivo whitelist.json
    whitelist_path = os.path.join(server.minecraft_data_path, 'whitelist.json')
    
    try:
        if os.path.exists(whitelist_path):
            with open(whitelist_path, 'r') as f:
                whitelist = json.load(f)
            # Asegurar que es una lista de objetos con 'name'
            if isinstance(whitelist, list):
                return JsonResponse({'success': True, 'data': whitelist})
            else:
                return JsonResponse({'success': True, 'data': []})
        else:
            return JsonResponse({'success': True, 'data': []})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def switch_server(request):
    """
    [DEPRECATED] Guardar sesión de servidor (opcional)
    
    NOTA: Este endpoint es opcional. El cliente debe enviar siempre server_id
    en cada request (URL, query param o header X-Server-ID).
    Este endpoint solo guarda una sesión para mostrar "último servidor usado".
    """
    try:
        server_id = _get_server_id_from_request(request)
        
        if not server_id:
            return JsonResponse({'success': False, 'error': 'Server ID required (send in URL, query param, header X-Server-ID, or body)'}, status=400)
        
        server = get_object_or_404(Server, id=server_id, is_active=True)
        user_role = UserServerRole.objects.filter(user=request.user, server=server).first()
        
        if not user_role:
            return JsonResponse({'success': False, 'error': 'No access to this server'}, status=403)
        
        # Actualizar o crear sesión (opcional, solo para historial)
        from ..models.models_multi import ServerSession
        ServerSession.objects.update_or_create(
            user=request.user,
            server=server,
            defaults={'last_accessed': timezone.now()}
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Session saved for server {server.name}',
            'server': {
                'id': server.id,
                'name': server.name,
                'host': server.host,
                'role': user_role.role,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def saved_sessions(request):
    """Obtener lista de sesiones de servidores guardadas para el usuario"""
    from ..models.models_multi import ServerSession
    sessions = ServerSession.objects.filter(user=request.user).select_related('server').order_by('-last_accessed')
    data = [{
        'id': s.server.id,
        'name': s.server.name,
        'host': s.server.host,
        'last_accessed': s.last_accessed.isoformat(),
        'is_favorite': s.is_favorite,
    } for s in sessions]
    return JsonResponse({'success': True, 'data': data})

@login_required
@require_http_methods(["GET"])
def security_logs(request):
    """Obtener logs de seguridad (intentos de login, etc.)"""
    from ..models import SecurityLog
    
    # Solo admins pueden ver logs de seguridad
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    # Parámetros de filtrado
    log_type = request.GET.get('log_type', None)
    limit = int(request.GET.get('limit', 50))
    
    logs = SecurityLog.objects.all()
    
    if log_type:
        logs = logs.filter(log_type=log_type)
    
    logs = logs.order_by('-created_at')[:limit]
    
    data = [{
        'id': log.id,
        'log_type': log.log_type,
        'ip_address': str(log.ip_address) if log.ip_address else None,
        'details': log.details,
        'created_at': log.created_at.isoformat(),
    } for log in logs]
    
    return JsonResponse({
        'success': True,
        'data': data,
        'total': SecurityLog.objects.count()
    })
