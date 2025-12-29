from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import models
from django.utils import timezone
import json
import os
from pathlib import Path
import mcrcon
from django.conf import settings

def dashboard(request):
    """Panel principal - Detectar servidor automáticamente o mostrar selector"""
    # Si no está autenticado, redirigir a login
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    
    from ..models import Server, UserServerRole
    from ..models.models_multi import ServerSession
    
    # Obtener servidor desde parámetro (cambio manual) o detección automática
    server_id = request.GET.get('server_id')
    detected_server = None
    
    if server_id:
        # Usuario seleccionó un servidor específico
        try:
            detected_server = Server.objects.get(id=server_id, is_active=True)
            # Guardar sesión
            ServerSession.objects.update_or_create(
                user=request.user,
                server=detected_server,
                defaults={'last_accessed': timezone.now()}
            )
        except Server.DoesNotExist:
            pass
    else:
        # Detectar servidor por hostname/IP de la request
        server_host = _detect_server_from_request(request)
        if server_host:
            try:
                # Buscar servidor por host exacto o por IPs conocidas
                detected_server = Server.objects.filter(host=server_host, is_active=True).first()
                
                # Si no se encuentra, buscar por IPs conocidas (Tailscale, local)
                if not detected_server:
                    # Detect server by hostname/IP (configurable via environment)
                    server_hosts = os.environ.get('SERVER_HOSTS', '').split(',')
                    if server_host in server_hosts or server_host in ['localhost', '127.0.0.1']:
                        # Si es el dominio central, usar servidor por defecto del usuario
                        from ..models.models_multi import UserPreference
                        try:
                            pref = UserPreference.objects.get(user=request.user)
                            if pref.default_server:
                                detected_server = pref.default_server
                        except:
                            # Si no hay preferencia, usar el primero disponible
                            detected_server = Server.objects.filter(is_active=True).first()
                
                if detected_server:
                    # Guardar sesión
                    ServerSession.objects.update_or_create(
                        user=request.user,
                        server=detected_server,
                        defaults={'last_accessed': timezone.now()}
                    )
            except Exception as e:
                print(f"Error in dashboard: {e}")
                pass
    
    # Obtener servidores disponibles para el usuario
    user_servers = UserServerRole.objects.filter(
        user=request.user
    ).select_related('server').filter(server__is_active=True)
    
    # Obtener sesiones guardadas
    saved_sessions = ServerSession.objects.filter(
        user=request.user
    ).select_related('server').order_by('-last_accessed')[:5]
    
    # Si se detectó un servidor, verificar acceso
    context = {
        'server': None,
        'available_servers': [],
        'saved_sessions': [],
        'is_central_panel': os.environ.get('CENTRAL_PANEL_HOST', '') in request.get_host(),
    }
    
    if detected_server:
        user_role = UserServerRole.objects.filter(
            user=request.user, 
            server=detected_server
        ).first()
        if user_role:
            context['server'] = {
                'id': detected_server.id,
                'name': detected_server.name,
                'host': detected_server.host,
                'role': user_role.role,
            }
    
    # Listar servidores disponibles
    for user_role in user_servers:
        context['available_servers'].append({
            'id': user_role.server.id,
            'name': user_role.server.name,
            'host': user_role.server.host,
            'role': user_role.role,
        })
    
    # Listar sesiones guardadas
    for session in saved_sessions:
        context['saved_sessions'].append({
            'id': session.server.id,
            'name': session.server.name,
            'host': session.server.host,
            'last_accessed': session.last_accessed,
            'is_favorite': session.is_favorite,
        })
    
    return render(request, 'panel/dashboard.html', context)

def _detect_server_from_request(request):
    """Detectar servidor desde la request (hostname/IP)"""
    host = request.get_host().split(':')[0]  # Remover puerto si existe
    
    # Buscar servidor por host exacto o parcial
    try:
        from ..models import Server
        # Primero buscar coincidencia exacta
        server = Server.objects.filter(host=host, is_active=True).first()
        
        if not server:
            # Buscar por coincidencia parcial (IP sin puerto)
            server = Server.objects.filter(
                models.Q(host__startswith=host) | models.Q(host__contains=host),
                is_active=True
            ).first()
        
        # Si no se encuentra, buscar por IPs conocidas (Tailscale, local)
        if not server:
            # Detect local network access (configurable via environment)
            local_hosts = os.environ.get('LOCAL_HOSTS', 'localhost,127.0.0.1').split(',')
            if host in local_hosts:
                server = Server.objects.filter(is_active=True).first()
        
        if server:
            return server.host
    except Exception as e:
        print(f"Error detecting server: {e}")
        pass
    
    return None

def _get_rcon_connection(server=None):
    """Conectar a RCON - Soporta servidor específico o configuración global"""
    try:
        if server:
            # Usar configuración del servidor desde BD
            rcon = mcrcon.MCRcon(server.host, server.rcon_password, port=server.rcon_port)
        else:
            # Usar configuración global (compatibilidad)
            rcon = mcrcon.MCRcon(settings.RCON_HOST, settings.RCON_PASSWORD, port=settings.RCON_PORT)
        rcon.connect()
        return rcon
    except Exception as e:
        print(f"RCON Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

@login_required
@require_http_methods(["GET"])
def whitelist_api(request):
    """Obtener lista de usuarios en whitelist"""
    try:
        whitelist_path = settings.WHITELIST_PATH
        if os.path.exists(whitelist_path):
            with open(whitelist_path, 'r') as f:
                whitelist = json.load(f)
            return JsonResponse({'success': True, 'data': whitelist})
        else:
            return JsonResponse({'success': False, 'error': 'Whitelist file not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def whitelist_action(request, action):
    """Agregar o eliminar usuario de whitelist - Requiere header X-Server-ID"""
    from .models import Server
    
    try:
        server_id = _get_server_id_from_request(request)
        
        if not server_id:
            return JsonResponse({
                'success': False, 
                'error': 'Server ID required. Send header X-Server-ID: <id>'
            }, status=400)
        
        try:
            server = Server.objects.get(id=server_id, is_active=True)
        except Server.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Server not found'}, status=404)
        
        # Verificar permisos
        from ..models import UserServerRole
        user_role = UserServerRole.objects.filter(user=request.user, server=server).first()
        if not user_role:
            return JsonResponse({'success': False, 'error': 'No access to this server'}, status=403)
        
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        
        if not username:
            return JsonResponse({'success': False, 'error': 'Username required'})
        
        rcon = _get_rcon_connection(server)
        if rcon is None:
            return JsonResponse({
                'success': False, 
                'error': f'Cannot connect to RCON. Server: {server.name}, Host: {server.host}, Port: {server.rcon_port}'
            }, status=500)
        
        try:
            if action == 'add':
                response = rcon.command(f'whitelist add {username}')
                return JsonResponse({'success': True, 'message': f'User {username} added to whitelist', 'response': response})
            elif action == 'remove':
                response = rcon.command(f'whitelist remove {username}')
                return JsonResponse({'success': True, 'message': f'User {username} removed from whitelist', 'response': response})
            else:
                return JsonResponse({'success': False, 'error': 'Invalid action'})
        finally:
            try:
                rcon.disconnect()
            except:
                pass
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'RCON error: {str(e)}'})

# Importar helper común desde utils
from ..utils.permissions import _get_server_id_from_request

@login_required
@require_http_methods(["GET"])
def mods_api(request):
    """Obtener lista de mods instalados - Requiere header X-Server-ID"""
    try:
        server_id = _get_server_id_from_request(request)
        
        if not server_id:
            return JsonResponse({
                'success': False, 
                'error': 'Server ID required. Send header X-Server-ID: <id>'
            }, status=400)
        
        try:
            server = Server.objects.get(id=server_id, is_active=True)
        except Server.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Server not found'}, status=404)
        
        # Verificar permisos
        from ..models import UserServerRole
        user_role = UserServerRole.objects.filter(user=request.user, server=server).first()
        if not user_role:
            return JsonResponse({'success': False, 'error': 'No access to this server'}, status=403)
        
        mods_path = os.path.join(server.minecraft_data_path, 'mods')
        mods = []
        if os.path.exists(mods_path):
            for file in os.listdir(mods_path):
                if file.endswith('.jar'):
                    file_path = os.path.join(mods_path, file)
                    size = os.path.getsize(file_path)
                    mods.append({
                        'name': file,
                        'size': size,
                        'size_mb': round(size / (1024 * 1024), 2)
                    })
        return JsonResponse({'success': True, 'data': mods})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def mods_action(request, action):
    """Agregar o eliminar mod - Requiere header X-Server-ID"""
    try:
        server_id = _get_server_id_from_request(request)
        
        if not server_id:
            return JsonResponse({
                'success': False, 
                'error': 'Server ID required. Send header X-Server-ID: <id>'
            }, status=400)
        
        try:
            server = Server.objects.get(id=server_id, is_active=True)
        except Server.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Server not found'}, status=404)
        
        # Verificar permisos
        from ..models import UserServerRole
        user_role = UserServerRole.objects.filter(user=request.user, server=server).first()
        if not user_role:
            return JsonResponse({'success': False, 'error': 'No access to this server'}, status=403)
        
        mods_path = os.path.join(server.minecraft_data_path, 'mods')
        os.makedirs(mods_path, exist_ok=True)
        
        if action == 'delete':
            data = json.loads(request.body)
            mod_name = data.get('mod_name', '').strip()
            
            if not mod_name:
                return JsonResponse({'success': False, 'error': 'Mod name required'})
            
            # Validar que es un nombre de archivo seguro
            if '..' in mod_name or '/' in mod_name or '\\' in mod_name:
                return JsonResponse({'success': False, 'error': 'Invalid mod name'})
            
            mod_path = os.path.join(mods_path, mod_name)
            if os.path.exists(mod_path):
                os.remove(mod_path)
                return JsonResponse({'success': True, 'message': f'Mod {mod_name} deleted'})
            else:
                return JsonResponse({'success': False, 'error': 'Mod not found'})
        
        elif action == 'upload':
            if 'mod_file' not in request.FILES:
                return JsonResponse({'success': False, 'error': 'No file provided'})
            
            file = request.FILES['mod_file']
            if not file.name.endswith('.jar'):
                return JsonResponse({'success': False, 'error': 'Only .jar files allowed'})
            
            # Validar tamaño (max 200MB)
            if file.size > 200 * 1024 * 1024:
                return JsonResponse({'success': False, 'error': 'File too large (max 200MB)'})
            
            mod_path = os.path.join(mods_path, file.name)
            with open(mod_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            
            return JsonResponse({'success': True, 'message': f'Mod {file.name} uploaded successfully'})
        
        else:
            return JsonResponse({'success': False, 'error': 'Invalid action'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["GET"])
def players_api(request):
    """Obtener lista de jugadores online - Requiere header X-Server-ID"""
    try:
        server_id = _get_server_id_from_request(request)
        
        if not server_id:
            return JsonResponse({
                'success': False, 
                'error': 'Server ID required. Send header X-Server-ID: <id>'
            }, status=400)
        
        try:
            server = Server.objects.get(id=server_id, is_active=True)
        except Server.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Server not found'}, status=404)
        
        # Verificar permisos
        from ..models import UserServerRole
        user_role = UserServerRole.objects.filter(user=request.user, server=server).first()
        if not user_role:
            return JsonResponse({'success': False, 'error': 'No access to this server'}, status=403)
        
        rcon = _get_rcon_connection(server)
        if rcon is None:
            return JsonResponse({'success': False, 'error': f'Cannot connect to RCON. Server: {server.name}, Host: {server.host}, Port: {server.rcon_port}'})
        
        try:
            response = rcon.command('list')
            # Parsear respuesta de "list" command
            # Formato: "There are X of a max of Y players online: player1, player2"
            players = []
            if 'online:' in response:
                players_str = response.split('online:')[1].strip()
                if players_str and players_str != '':
                    players = [p.strip() for p in players_str.split(',') if p.strip()]
            
            return JsonResponse({'success': True, 'data': players})
        finally:
            try:
                rcon.disconnect()
            except:
                pass
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'RCON error: {str(e)}'})

@login_required
@require_http_methods(["GET"])
def logs_api(request):
    """Obtener logs recientes del servidor - Requiere header X-Server-ID"""
    from .models import Server  # Import Server here to avoid circular imports
    
    try:
        server_id = _get_server_id_from_request(request)
        
        if not server_id:
            return JsonResponse({
                'success': False, 
                'error': 'Server ID required. Send header X-Server-ID: <id>'
            }, status=400)
        
        try:
            server = Server.objects.get(id=server_id, is_active=True)
        except Server.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Server not found'}, status=404)
        
        # Verificar permisos
        from ..models import UserServerRole
        user_role = UserServerRole.objects.filter(user=request.user, server=server).first()
        if not user_role:
            return JsonResponse({'success': False, 'error': 'No access to this server'}, status=403)
        
        logs_dir = os.path.join(server.minecraft_data_path, 'logs')
        latest_log = os.path.join(logs_dir, 'latest.log')
        
        # Intentar leer latest.log primero
        if os.path.exists(latest_log):
            with open(latest_log, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                recent_logs = lines[-100:] if len(lines) > 100 else lines
            return JsonResponse({'success': True, 'data': recent_logs})
        
        # Si no existe latest.log, buscar el log más reciente
        if os.path.exists(logs_dir):
            import glob
            log_files = glob.glob(os.path.join(logs_dir, '*.log'))
            if not log_files:
                # Buscar logs comprimidos
                log_files = glob.glob(os.path.join(logs_dir, '*.log.gz'))
                if log_files:
                    # Ordenar por fecha de modificación
                    log_files.sort(key=os.path.getmtime, reverse=True)
                    # Leer el más reciente (descomprimir si es .gz)
                    import gzip
                    with gzip.open(log_files[0], 'rt', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        recent_logs = lines[-100:] if len(lines) > 100 else lines
                    return JsonResponse({'success': True, 'data': recent_logs})
            
            if log_files:
                # Ordenar por fecha de modificación
                log_files.sort(key=os.path.getmtime, reverse=True)
                with open(log_files[0], 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    recent_logs = lines[-100:] if len(lines) > 100 else lines
                return JsonResponse({'success': True, 'data': recent_logs})
        
        return JsonResponse({'success': False, 'error': 'Log file not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def command_api(request):
    """Ejecutar comando en el servidor vía RCON - Requiere header X-Server-ID"""
    try:
        server_id = _get_server_id_from_request(request)
        
        if not server_id:
            return JsonResponse({
                'success': False, 
                'error': 'Server ID required. Send header X-Server-ID: <id>'
            }, status=400)
        
        try:
            server = Server.objects.get(id=server_id, is_active=True)
        except Server.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Server not found'}, status=404)
        
        # Verificar permisos
        from ..models import UserServerRole
        user_role = UserServerRole.objects.filter(user=request.user, server=server).first()
        if not user_role:
            return JsonResponse({'success': False, 'error': 'No access to this server'}, status=403)
        
        data = json.loads(request.body)
        command = data.get('command', '').strip()
        
        if not command:
            return JsonResponse({'success': False, 'error': 'Command required'})
        
        # Comandos permitidos (seguridad)
        allowed_commands = ['list', 'whitelist', 'say', 'kick', 'ban', 'pardon', 'op', 'deop']
        command_base = command.split()[0] if command.split() else ''
        
        if command_base not in allowed_commands:
            return JsonResponse({'success': False, 'error': f'Command {command_base} not allowed'})
        
        rcon = _get_rcon_connection(server)
        if rcon is None:
            return JsonResponse({'success': False, 'error': f'Cannot connect to RCON. Server: {server.name}, Host: {server.host}, Port: {server.rcon_port}'})
        
        try:
            response = rcon.command(command)
            return JsonResponse({'success': True, 'response': response})
        finally:
            try:
                rcon.disconnect()
            except:
                pass
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

