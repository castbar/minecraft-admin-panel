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
    """Conectar a RCON para un servidor específico - Usa subprocess para evitar problemas con signals en threads"""
    import subprocess
    import socket
    
    class RconWrapper:
        """Wrapper para RCON que usa subprocess para evitar problemas con signals"""
        def __init__(self, host, port, password):
            self.host = host
            self.port = port
            self.password = password
            self.connected = False
            
        def connect(self):
            """Verificar que podemos conectarnos al puerto RCON"""
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((self.host, self.port))
                sock.close()
                if result == 0:
                    self.connected = True
                    return True
                return False
            except Exception as e:
                print(f"Error checking RCON connection: {e}")
                return False
                
        def command(self, cmd):
            """Ejecutar comando RCON usando mcrcon library primero, luego socket como fallback"""
            try:
                # Intentar usar la librería mcrcon directamente primero (más confiable)
                # pero capturar el error de signal y usar socket como fallback
                try:
                    rcon = mcrcon.MCRcon(self.host, self.password, port=self.port)
                    rcon.connect()
                    response = rcon.command(cmd)
                    rcon.disconnect()
                    return response
                except ValueError as e:
                    if "signal only works in main thread" in str(e):
                        # Si falla por signal, usar socket directamente
                        print(f"mcrcon library failed due to signal issue, using socket: {e}")
                        return self._command_via_socket(cmd)
                    raise
                except Exception as e:
                    # Si hay otro error con mcrcon, intentar socket
                    print(f"mcrcon library failed, trying socket: {e}")
                    return self._command_via_socket(cmd)
            except Exception as e:
                print(f"Error executing RCON command: {e}")
                raise
                
        def _command_via_socket(self, cmd):
            """Ejecutar comando RCON usando socket directamente (sin signals) - Implementación correcta del protocolo RCON"""
            import struct
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)
                sock.connect((self.host, self.port))
                
                # Protocolo RCON: cada paquete tiene:
                # - Length (4 bytes, little-endian): tamaño del resto del paquete (sin incluir este campo)
                # - Request ID (4 bytes, little-endian)
                # - Type (4 bytes, little-endian): 3 = AUTH, 2 = COMMAND, 0 = RESPONSE
                # - Body (string null-terminated)
                # - Null terminator (1 byte)
                
                # 1. Autenticación
                request_id = 0
                auth_type = 3  # AUTH
                auth_body = (self.password + '\x00').encode('utf-8')
                auth_packet_body = struct.pack('<ii', request_id, auth_type) + auth_body
                auth_packet_length = struct.pack('<i', len(auth_packet_body))
                auth_packet = auth_packet_length + auth_packet_body
                
                sock.sendall(auth_packet)
                
                # Recibir respuesta de autenticación
                auth_response_length = struct.unpack('<i', sock.recv(4))[0]
                auth_response = sock.recv(auth_response_length)
                
                if len(auth_response) < 8:
                    raise Exception("Invalid authentication response")
                
                auth_resp_id, auth_resp_type = struct.unpack('<ii', auth_response[0:8])
                
                # Si request_id es -1, la autenticación falló
                if auth_resp_id == -1:
                    raise Exception("RCON authentication failed")
                
                # 2. Enviar comando
                cmd_request_id = 1
                cmd_type = 2  # COMMAND
                cmd_body = (cmd + '\x00').encode('utf-8')
                cmd_packet_body = struct.pack('<ii', cmd_request_id, cmd_type) + cmd_body
                cmd_packet_length = struct.pack('<i', len(cmd_packet_body))
                cmd_packet = cmd_packet_length + cmd_packet_body
                
                sock.sendall(cmd_packet)
                
                # 3. Recibir respuesta (puede venir en múltiples paquetes)
                response_data = b''
                while True:
                    # Leer length
                    length_bytes = sock.recv(4)
                    if len(length_bytes) < 4:
                        break
                    
                    length = struct.unpack('<i', length_bytes)[0]
                    if length == 0:
                        break
                    
                    # Leer el resto del paquete
                    packet_data = b''
                    while len(packet_data) < length:
                        chunk = sock.recv(length - len(packet_data))
                        if not chunk:
                            break
                        packet_data += chunk
                    
                    if len(packet_data) >= 8:
                        resp_id, resp_type = struct.unpack('<ii', packet_data[0:8])
                        # Si es el último paquete (type 0 y request_id coincide), o si recibimos menos datos
                        if resp_type == 0 or len(packet_data) < length:
                            if len(packet_data) > 8:
                                response_data += packet_data[8:]
                            break
                        else:
                            # Agregar el body de este paquete
                            if len(packet_data) > 8:
                                response_data += packet_data[8:]
                
                sock.close()
                
                # Parsear respuesta
                if response_data:
                    # Remover null terminators
                    text = response_data.rstrip(b'\x00').decode('utf-8', errors='ignore')
                    return text
                return ""
            except Exception as e:
                print(f"Error in socket-based RCON: {e}")
                import traceback
                traceback.print_exc()
                raise
                
        def disconnect(self):
            """Cerrar conexión"""
            self.connected = False
    
    try:
        # Log para debugging
        print(f"🔌 Intentando conectar RCON: host={server.host}, port={server.rcon_port}")
        
        # Si el host es un nombre de contenedor Docker, usar ese nombre directamente
        # Si es una IP, usar la IP
        host = server.host
        
        rcon = RconWrapper(host, server.rcon_port, server.rcon_password)
        if rcon.connect():
            print(f"✅ RCON conectado exitosamente a {server.name} (host: {host})")
            return rcon
        else:
            print(f"❌ No se pudo conectar a RCON para {server.name}")
            return None
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
    
    # Obtener estado del contenedor Docker usando la librería docker de Python
    container_status = None
    is_running = False
    
    if server.container_name:
        try:
            # Usar la librería docker de Python directamente
            client = docker.from_env()
            container = client.containers.get(server.container_name)
            container_status = container.status
            is_running = container_status == 'running'
        except docker.errors.NotFound:
            container_status = 'not_found'
            is_running = False
        except Exception as e:
            print(f"Error getting container status for {server.container_name}: {e}")
            # Fallback: intentar con get_container_status (puede fallar si no hay comando docker)
            try:
                container_status = get_container_status(server.container_name)
                is_running = container_status == 'running' if container_status else False
            except:
                container_status = None
                is_running = False
    
    # Intentar conectar vía RCON para verificar estado de Minecraft (solo si el contenedor está corriendo)
    is_rcon_connected = False
    rcon = None
    if is_running:
        rcon = _get_rcon_connection(server)
        is_rcon_connected = rcon is not None
    is_online = is_rcon_connected
    
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
    
    if server.container_name and is_running:
        try:
            # Reutilizar el cliente docker si ya lo tenemos, sino crear uno nuevo
            try:
                container = client.containers.get(server.container_name)
            except NameError:
                # Si client no existe, crearlo
                client = docker.from_env()
                container = client.containers.get(server.container_name)
            except Exception:
                # Si falla, crear un nuevo cliente
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
            'is_running': is_running,
            'is_rcon_connected': is_rcon_connected,
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
def players_online(request, server_id=None):
    """Obtener lista de jugadores conectados - Requiere header X-Server-ID"""
    resolved_server_id = _get_server_id_from_request(request) or server_id
    if not resolved_server_id:
        return JsonResponse({
            'success': False, 
            'error': 'Server ID required. Send header X-Server-ID: <id>'
        }, status=400)
    
    server, error_response = _check_server_permission(request, resolved_server_id, 'view')
    if error_response:
        return error_response
    
    rcon = _get_rcon_connection(server)
    players = []
    player_count = 0
    max_players = 20
    
    print(f"players_online - RCON connection: {rcon is not None}")
    
    if rcon:
        try:
            response = rcon.command('list')
            print(f"players_online - RCON list response: {response}")
            
            # Parsear jugadores
            if 'online:' in response:
                players_str = response.split('online:')[1].strip()
                print(f"players_online - Players string: '{players_str}'")
                if players_str:
                    players = [p.strip() for p in players_str.split(',') if p.strip()]
                    player_count = len(players)
                    print(f"players_online - Parsed players: {players}, count: {player_count}")
            else:
                print(f"players_online - No 'online:' found in response")
            
            # Obtener max players
            if 'of a max of' in response:
                try:
                    max_players = int(response.split('of a max of')[1].split()[0])
                    print(f"players_online - Max players: {max_players}")
                except Exception as e:
                    print(f"players_online - Error parsing max players: {e}")
            else:
                print(f"players_online - No 'of a max of' found in response")
        except Exception as e:
            print(f"players_online - Exception: {e}")
            import traceback
            traceback.print_exc()
            send_notification(server, 'rcon_error', f"Error al obtener lista de jugadores: {e}")
        finally:
            if rcon:
                try:
                    rcon.disconnect()
                except Exception as e:
                    print(f"players_online - Error disconnecting RCON: {e}")
    else:
        print(f"players_online - RCON connection failed for server {server.name} (host: {server.host}, port: {server.rcon_port})")
    
    print(f"players_online - Returning: players={players}, player_count={player_count}, max_players={max_players}")
    
    return JsonResponse({
        'success': True,
        'data': {
            'players': players,
            'player_count': player_count,
            'max_players': max_players
        }
    })

@login_required
@require_http_methods(["GET"])
def server_logs(request, server_id=None):
    """Obtener logs recientes del servidor - Requiere header X-Server-ID"""
    import os
    import glob
    import gzip
    
    resolved_server_id = _get_server_id_from_request(request) or server_id
    if not resolved_server_id:
        return JsonResponse({
            'success': False, 
            'error': 'Server ID required. Send header X-Server-ID: <id>'
        }, status=400)
    
    server, error_response = _check_server_permission(request, resolved_server_id, 'view')
    if error_response:
        return error_response
    
    # Obtener número de líneas del parámetro (por defecto 100)
    lines_param = request.GET.get('lines', '100')
    try:
        num_lines = int(lines_param)
    except ValueError:
        num_lines = 100
    
    try:
        # Si el servidor tiene un container_name, leer logs desde el contenedor Docker
        if server.container_name:
            logs_path = os.path.join(server.minecraft_data_path, 'logs', 'latest.log')
            print(f"🔍 server_logs - Container: {server.container_name}, Path: {logs_path}")
            
            # Intentar leer latest.log desde el contenedor usando la librería docker de Python
            try:
                # Verificar que el contenedor existe y está corriendo
                container_status = get_container_status(server.container_name)
                print(f"🔍 server_logs - Container status: {container_status}")
                
                # Intentar acceder al contenedor directamente, incluso si get_container_status falla
                # porque puede que el contenedor esté en otra red o el método de verificación falle
                try:
                    client = docker.from_env()
                    container = client.containers.get(server.container_name)
                    container_status_actual = container.status
                    print(f"🔍 server_logs - Direct container status: {container_status_actual}")
                except Exception as e:
                    print(f"⚠️ server_logs - Could not get container directly: {e}")
                    container = None
                
                if container and (container_status == 'running' or container.status == 'running'):
                    # Usar la librería docker de Python para ejecutar comandos en el contenedor
                    try:
                        print(f"🔍 server_logs - Connecting to Docker...")
                        client = docker.from_env()
                        container = client.containers.get(server.container_name)
                        print(f"🔍 server_logs - Container found, executing tail...")
                        
                        # Ejecutar tail -n N en el contenedor
                        exec_result = container.exec_run(
                            f'tail -n {num_lines} {logs_path}',
                            user='minecraft'
                        )
                        
                        print(f"🔍 server_logs - Tail exit code: {exec_result.exit_code}")
                        
                        if exec_result.exit_code == 0:
                            # Dividir en líneas y retornar
                            lines = exec_result.output.decode('utf-8', errors='ignore').split('\n')
                            # Filtrar líneas vacías al final
                            while lines and not lines[-1]:
                                lines.pop()
                            print(f"🔍 server_logs - Returning {len(lines)} lines from container")
                            return JsonResponse({'success': True, 'data': lines})
                        else:
                            print(f"🔍 server_logs - Tail failed, trying cat...")
                            # Si tail falla, intentar leer el archivo completo con cat
                            exec_result = container.exec_run(
                                f'cat {logs_path}',
                                user='minecraft'
                            )
                            
                            print(f"🔍 server_logs - Cat exit code: {exec_result.exit_code}")
                            
                            if exec_result.exit_code == 0:
                                lines = exec_result.output.decode('utf-8', errors='ignore').split('\n')
                                # Filtrar líneas vacías al final
                                while lines and not lines[-1]:
                                    lines.pop()
                                # Tomar las últimas N líneas
                                recent_logs = lines[-num_lines:] if len(lines) > num_lines else lines
                                print(f"🔍 server_logs - Returning {len(recent_logs)} lines from cat")
                                return JsonResponse({'success': True, 'data': recent_logs})
                            else:
                                print(f"🔍 server_logs - Cat also failed, output: {exec_result.output.decode('utf-8', errors='ignore')[:200]}")
                    except docker.errors.NotFound as e:
                        print(f"❌ server_logs - Container {server.container_name} not found: {e}")
                        # Contenedor no encontrado, devolver array vacío
                        return JsonResponse({'success': True, 'data': [], 'server_status': 'not_found'})
                    except docker.errors.APIError as e:
                        print(f"❌ server_logs - Docker API error: {e}")
                        # Error de Docker, devolver array vacío
                        return JsonResponse({'success': True, 'data': [], 'server_status': 'error'})
                    except Exception as e:
                        print(f"❌ server_logs - Error reading logs from container: {e}")
                        import traceback
                        traceback.print_exc()
                        # Error al leer logs, devolver array vacío
                        return JsonResponse({'success': True, 'data': [], 'server_status': 'error'})
                else:
                    print(f"⚠️ server_logs - Container {server.container_name} is not running (status: {container_status})")
                    # Servidor apagado, devolver array vacío en lugar de continuar
                    return JsonResponse({'success': True, 'data': [], 'server_status': container_status or 'stopped'})
            except Exception as e:
                # Si falla docker, continuar con el método de sistema de archivos local
                print(f"❌ server_logs - Error accessing Docker: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"⚠️ server_logs - Server {server.id} has no container_name")
        
        # Fallback: intentar leer desde el sistema de archivos local
        logs_dir = os.path.join(server.minecraft_data_path, 'logs')
        latest_log = os.path.join(logs_dir, 'latest.log')
        print(f"🔍 server_logs - Fallback: checking local filesystem at {latest_log}")
        print(f"🔍 server_logs - File exists: {os.path.exists(latest_log)}")
        
        # Fallback: intentar leer desde el sistema de archivos local
        logs_dir = os.path.join(server.minecraft_data_path, 'logs')
        latest_log = os.path.join(logs_dir, 'latest.log')
        
        # Intentar leer latest.log primero
        if os.path.exists(latest_log):
            try:
                with open(latest_log, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    recent_logs = lines[-num_lines:] if len(lines) > num_lines else lines
                return JsonResponse({'success': True, 'data': recent_logs})
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Error reading log file: {str(e)}'}, status=500)
        
        # Si no existe latest.log, buscar el log más reciente
        if os.path.exists(logs_dir):
            log_files = glob.glob(os.path.join(logs_dir, '*.log'))
            if not log_files:
                # Buscar logs comprimidos
                log_files = glob.glob(os.path.join(logs_dir, '*.log.gz'))
                if log_files:
                    # Ordenar por fecha de modificación
                    log_files.sort(key=os.path.getmtime, reverse=True)
                    # Leer el más reciente (descomprimir si es .gz)
                    try:
                        with gzip.open(log_files[0], 'rt', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            recent_logs = lines[-num_lines:] if len(lines) > num_lines else lines
                        return JsonResponse({'success': True, 'data': recent_logs})
                    except Exception as e:
                        return JsonResponse({'success': False, 'error': f'Error reading compressed log: {str(e)}'}, status=500)
            
            if log_files:
                # Ordenar por fecha de modificación
                log_files.sort(key=os.path.getmtime, reverse=True)
                try:
                    with open(log_files[0], 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        recent_logs = lines[-num_lines:] if len(lines) > num_lines else lines
                    return JsonResponse({'success': True, 'data': recent_logs})
                except Exception as e:
                    return JsonResponse({'success': False, 'error': f'Error reading log file: {str(e)}'}, status=500)
        
        # Si no se encontraron logs, verificar si el servidor está apagado
        # Si el contenedor está apagado o no existe, devolver array vacío en lugar de error
        if server.container_name:
            try:
                container_status = get_container_status(server.container_name)
                if container_status in ['stopped', 'not_found', None]:
                    # Servidor apagado, devolver array vacío
                    return JsonResponse({'success': True, 'data': [], 'server_status': container_status or 'unknown'})
            except:
                pass
        
        # Si llegamos aquí y no hay logs, devolver array vacío en lugar de error 404
        return JsonResponse({'success': True, 'data': [], 'message': 'No logs available'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        # En caso de error, también devolver array vacío para evitar errores constantes
        return JsonResponse({'success': True, 'data': [], 'error': str(e)})

@login_required
@require_http_methods(["GET"])
def server_stats(request, server_id=None):
    """Obtener estadísticas actuales del servidor (CPU, memoria) - Requiere header X-Server-ID"""
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
    
    # Obtener estadísticas actuales del contenedor
    cpu_usage = None
    memory_usage = None
    memory_max = None
    
    if server.container_name:
        try:
            print(f"🔍 server_stats - Obteniendo stats para contenedor: {server.container_name}")
            client = docker.from_env()
            container = client.containers.get(server.container_name)
            print(f"🔍 server_stats - Estado del contenedor: {container.status}")
            
            if container.status == 'running':
                print(f"🔍 server_stats - Contenedor corriendo, obteniendo stats...")
                stats = container.stats(stream=False)
                
                # Calcular CPU
                if 'cpu_stats' in stats and 'precpu_stats' in stats:
                    cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
                    system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
                    if system_delta > 0:
                        num_cores = len(stats['cpu_stats']['cpu_usage'].get('percpu_usage', [1]))
                        cpu_usage = (cpu_delta / system_delta) * num_cores * 100
                        print(f"🔍 server_stats - CPU calculado: {cpu_usage}%")
                
                # Calcular memoria
                if 'memory_stats' in stats:
                    memory_usage = stats['memory_stats'].get('usage', 0)
                    memory_max = stats['memory_stats'].get('limit', 0)
                    print(f"🔍 server_stats - Memoria: {memory_usage} / {memory_max}")
                
                # Obtener TPS vía RCON si está disponible
                tps = None
                mspt = None  # Milliseconds per tick
                # Verificar conexión RCON
                rcon_check = _get_rcon_connection(server)
                is_rcon_connected = rcon_check is not None
                if is_rcon_connected:
                    try:
                        rcon = rcon_check
                        if rcon:
                            # Intentar obtener TPS usando diferentes comandos según el tipo de servidor
                            # Para servidores con Spark o Paper: /spark tps o /tps
                            # Para servidores vanilla: usar /debug start y luego /debug stop para calcular
                            try:
                                # Intentar comando /tps primero (Paper/Spigot)
                                tps_response = rcon.command('tps')
                                print(f"🔍 server_stats - TPS response: {tps_response}")
                                # Parsear respuesta como "TPS from last 1m, 5m, 15m: 20.0, 20.0, 20.0"
                                import re
                                tps_match = re.search(r'(\d+\.?\d*)', tps_response)
                                if tps_match:
                                    tps = float(tps_match.group(1))
                            except:
                                try:
                                    # Intentar comando /spark tps (si Spark está instalado)
                                    spark_response = rcon.command('spark tps')
                                    print(f"🔍 server_stats - Spark TPS response: {spark_response}")
                                    import re
                                    tps_match = re.search(r'(\d+\.?\d*)', spark_response)
                                    if tps_match:
                                        tps = float(tps_match.group(1))
                                except:
                                    pass
                            
                            # Intentar obtener MSPT (milliseconds per tick)
                            try:
                                # Comando /tps también puede mostrar MSPT
                                mspt_response = rcon.command('tps')
                                import re
                                mspt_match = re.search(r'(\d+\.?\d*)\s*ms', mspt_response, re.IGNORECASE)
                                if mspt_match:
                                    mspt = float(mspt_match.group(1))
                            except:
                                pass
                            
                            if rcon:
                                try:
                                    rcon.disconnect()
                                except:
                                    pass
                    except Exception as e:
                        print(f"⚠️ server_stats - Error obteniendo TPS: {e}")
            else:
                print(f"⚠️ server_stats - Contenedor no está corriendo (status: {container.status})")
        except docker.errors.NotFound:
            print(f"❌ server_stats - Contenedor {server.container_name} no encontrado")
        except Exception as e:
            print(f"❌ server_stats - Error obteniendo stats del contenedor: {e}")
            import traceback
            traceback.print_exc()
    
    # Calcular porcentaje de memoria
    memory_percent = None
    if memory_usage and memory_max and memory_max > 0:
        memory_percent = round((memory_usage / memory_max) * 100, 2)
    
    return JsonResponse({
        'success': True,
        'data': {
            'cpu_usage': round(cpu_usage, 2) if cpu_usage else None,
            'memory_usage': memory_usage,
            'memory_max': memory_max,
            'memory_usage_mb': round(memory_usage / (1024 * 1024), 2) if memory_usage else None,
            'memory_max_mb': round(memory_max / (1024 * 1024), 2) if memory_max else None,
            'memory_percent': memory_percent,
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
        result = None
        if action == 'start':
            result = start_container(server.container_name)
            
            # Si el contenedor no existe, intentar recrearlo automáticamente
            if result and result.get('status') == 'not_found':
                print(f"🔄 Contenedor {server.container_name} no existe, intentando recrearlo automáticamente...")
                try:
                    from ..utils.docker_control import create_minecraft_container
                    
                    # Obtener puerto de Minecraft (por defecto 25565)
                    minecraft_port = 25565
                    
                    # Recrear el contenedor con las configuraciones guardadas
                    create_result = create_minecraft_container(
                        container_name=server.container_name,
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
                        start_container=True,  # Iniciar automáticamente
                        additional_ports=server.additional_ports or []
                    )
                    
                    if create_result.get('success'):
                        print(f"✅ Contenedor {server.container_name} recreado exitosamente")
                        send_notification(server, 'container_recreated', f"Contenedor para '{server.name}' fue recreado automáticamente y está iniciando.")
                        return JsonResponse({
                            'success': True,
                            'message': f'Contenedor recreado e iniciado correctamente. Los datos del servidor se han conservado.',
                            'container_recreated': True
                        })
                    else:
                        error_msg = create_result.get('error', 'Error desconocido al recrear contenedor')
                        print(f"❌ Error al recrear contenedor: {error_msg}")
                        send_notification(server, 'container_recreate_failed', f"No se pudo recrear el contenedor para '{server.name}': {error_msg}")
                        return JsonResponse({
                            'success': False,
                            'error': f'Contenedor no existe y no se pudo recrear: {error_msg}',
                            'container_recreated': False
                        }, status=500)
                except Exception as recreate_error:
                    error_msg = str(recreate_error)
                    print(f"❌ Excepción al recrear contenedor: {error_msg}")
                    send_notification(server, 'container_recreate_failed', f"Error al recrear contenedor para '{server.name}': {error_msg}")
                    return JsonResponse({
                        'success': False,
                        'error': f'Contenedor no existe y no se pudo recrear: {error_msg}',
                        'container_recreated': False
                    }, status=500)
        elif action == 'stop':
            result = stop_container(server.container_name)
        elif action == 'restart':
            result = restart_container(server.container_name)
        elif action == 'pause':
            result = pause_container(server.container_name)
        elif action == 'unpause':
            result = unpause_container(server.container_name)
        
        # Verificar resultado de la operación
        if result and result.get('success'):
            send_notification(server, 'server_control', f"Comando '{action}' ejecutado correctamente en '{server.name}'.")
            return JsonResponse({
                'success': True,
                'message': result.get('message', f'Server {action} command executed successfully')
            })
        else:
            error_msg = result.get('error', 'Error desconocido') if result else 'Error ejecutando comando'
            send_notification(server, 'server_control_failed', f"Fallo el comando '{action}' para '{server.name}': {error_msg}")
            return JsonResponse({
                'success': False,
                'error': error_msg
            }, status=500)
    except Exception as e:
        error_msg = str(e)
        send_notification(server, 'server_control_failed', f"Fallo el comando '{action}' para '{server.name}': {error_msg}")
        return JsonResponse({'success': False, 'error': error_msg}, status=500)

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
            print(f"RCON whitelist list response: {response}")
            # Parsear respuesta: "There are X whitelisted player(s): player1, player2"
            # También puede ser: "There are X whitelisted player(s):" (sin jugadores)
            players = []
            
            # Usar regex para extraer solo los nombres de jugadores después de ": "
            import re
            # Patrón: buscar ": " seguido de nombres separados por comas
            match = re.search(r':\s*([^:]+)$', response)
            if match:
                players_str = match.group(1).strip()
                if players_str:
                    # Separar por comas, limpiar espacios y filtrar vacíos
                    players = [p.strip() for p in players_str.split(',') if p.strip() and not p.strip().startswith('There are')]
            
            # Si no se encontraron con el primer método, intentar otro patrón
            if not players:
                # Buscar directamente después de "player(s):"
                match = re.search(r'player\(s\):\s*(.+)', response, re.IGNORECASE)
                if match:
                    players_str = match.group(1).strip()
                    if players_str:
                        players = [p.strip() for p in players_str.split(',') if p.strip() and not p.strip().startswith('There are')]
            
            # Eliminar duplicados manteniendo el orden
            seen = set()
            unique_players = []
            for p in players:
                if p not in seen:
                    seen.add(p)
                    unique_players.append(p)
            players = unique_players
            
            # Convertir a formato esperado por el frontend
            whitelist_data = [{'name': p, 'uuid': ''} for p in players]
            print(f"Parsed whitelist data: {whitelist_data} (total: {len(whitelist_data)})")
            return JsonResponse({'success': True, 'data': whitelist_data})
        except Exception as e:
            print(f"Error obteniendo whitelist vía RCON: {e}")
            import traceback
            traceback.print_exc()
            # Continuar al fallback
        finally:
            try:
                rcon.disconnect()
            except:
                pass
    else:
        print(f"RCON connection failed for server {server.name} (host: {server.host}, port: {server.rcon_port})")
    
    # Fallback: leer archivo whitelist.json
    whitelist_path = os.path.join(server.minecraft_data_path, 'whitelist.json')
    print(f"Trying to read whitelist file: {whitelist_path}")
    
    try:
        if os.path.exists(whitelist_path):
            with open(whitelist_path, 'r') as f:
                whitelist = json.load(f)
            print(f"Whitelist file content: {whitelist}")
            # Asegurar que es una lista de objetos con 'name'
            if isinstance(whitelist, list):
                # Si los objetos tienen 'name', usarlos directamente
                # Si son strings, convertirlos a objetos
                formatted_whitelist = []
                for item in whitelist:
                    if isinstance(item, dict):
                        formatted_whitelist.append({
                            'name': item.get('name', ''),
                            'uuid': item.get('uuid', '')
                        })
                    elif isinstance(item, str):
                        formatted_whitelist.append({
                            'name': item,
                            'uuid': ''
                        })
                return JsonResponse({'success': True, 'data': formatted_whitelist})
            else:
                print(f"Whitelist file is not a list: {type(whitelist)}")
                return JsonResponse({'success': True, 'data': []})
        else:
            print(f"Whitelist file does not exist: {whitelist_path}")
            # Si no hay archivo y RCON falló, devolver lista vacía
            return JsonResponse({'success': True, 'data': []})
    except Exception as e:
        print(f"Error reading whitelist file: {e}")
        import traceback
        traceback.print_exc()
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
