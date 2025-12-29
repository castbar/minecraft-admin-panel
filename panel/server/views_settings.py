from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import os
import re
from .models import Server, MinecraftUser
from .permissions import require_server_permission
# Importar función RCON desde views_api
try:
    from .views_api import _get_rcon_connection
except ImportError:
    # Fallback si no está disponible
    def _get_rcon_connection(server):
        import mcrcon
        try:
            rcon = mcrcon.MCRcon(server.host, server.rcon_password, port=server.rcon_port)
            rcon.connect()
            return rcon
        except:
            return None

@login_required
@require_server_permission('manage_settings')
@require_http_methods(["GET"])
def server_settings(request, server_id):
    """Obtener configuración del servidor"""
    server = request.server
    
    # Leer max-players y motd desde server.properties
    max_players = 20
    motd = "A Minecraft Server"
    server_properties_path = os.path.join(server.minecraft_data_path, 'server.properties')
    
    if os.path.exists(server_properties_path):
        with open(server_properties_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('max-players='):
                    try:
                        max_players = int(line.split('=')[1])
                    except:
                        pass
                elif line.startswith('motd='):
                    motd = line.split('=', 1)[1].replace('\\"', '"').replace('\\n', '\n')
    
    return JsonResponse({
        'success': True,
        'data': {
            'id': server.id,
            'name': server.name,
            'host': server.host,
            'is_public': server.is_public,
            'auth_mode': server.auth_mode,
            'auth_mode_display': server.get_auth_mode_display_short(),
            'enable_whitelist': server.enable_whitelist,
            'online_mode': server.online_mode,
            'is_active': server.is_active,
            'max_players': max_players,
            'motd': motd,
        }
    })

@login_required
@require_server_permission('manage_settings')
@require_http_methods(["POST"])
def server_settings_update(request, server_id):
    """Actualizar configuración del servidor"""
    server = request.server
    data = json.loads(request.body)
    
    # Campos actualizables
    updatable_fields = ['is_public', 'auth_mode', 'enable_whitelist', 'online_mode', 'max_players', 'motd']
    
    for field in updatable_fields:
        if field in data:
            setattr(server, field, data[field])
    
    server.save()
    
    # Aplicar cambios al servidor Minecraft
    _apply_server_settings(server, data)
    
    return JsonResponse({
        'success': True,
        'message': 'Server settings updated',
        'data': {
            'is_public': server.is_public,
            'auth_mode': server.auth_mode,
            'enable_whitelist': server.enable_whitelist,
            'online_mode': server.online_mode,
            'max_players': getattr(server, 'max_players', None),
            'motd': getattr(server, 'motd', None),
        }
    })

def _apply_server_settings(server, data=None):
    """Aplicar configuración al servidor Minecraft vía RCON o archivos"""
    import os
    import re
    # Importar función RCON desde views_api
    try:
        from .views_api import _get_rcon_connection
    except ImportError:
        # Fallback si no está disponible
        import mcrcon
        def _get_rcon_connection(server):
            try:
                rcon = mcrcon.MCRcon(server.host, server.rcon_password, port=server.rcon_port)
                rcon.connect()
                return rcon
            except:
                return None
    
    # Modificar server.properties para cambios que requieren reinicio
    server_properties_path = os.path.join(server.minecraft_data_path, 'server.properties')
    
    if os.path.exists(server_properties_path):
        # Leer archivo
        with open(server_properties_path, 'r') as f:
            content = f.read()
        
        # Aplicar cambios según los datos recibidos
        if data:
            # Max players - modificar server.properties
            if 'max_players' in data:
                max_players = data['max_players']
                content = re.sub(r'^max-players=.*$', f'max-players={max_players}', content, flags=re.MULTILINE)
            
            # MOTD - modificar server.properties
            if 'motd' in data:
                motd = data['motd'].replace('\\', '\\\\').replace('"', '\\"')
                content = re.sub(r'^motd=.*$', f'motd={motd}', content, flags=re.MULTILINE)
            
            # Online mode - modificar server.properties
            if 'online_mode' in data:
                online_mode = 'true' if data['online_mode'] else 'false'
                content = re.sub(r'^online-mode=.*$', f'online-mode={online_mode}', content, flags=re.MULTILINE)
            
            # Whitelist - puede activarse/desactivarse vía RCON
            if 'enable_whitelist' in data:
                enable_whitelist = data['enable_whitelist']
                content = re.sub(r'^white-list=.*$', f'white-list={str(enable_whitelist).lower()}', content, flags=re.MULTILINE)
                
                # Intentar aplicar vía RCON si el servidor está online
                rcon = _get_rcon_connection(server)
                if rcon:
                    try:
                        if enable_whitelist:
                            rcon.command('whitelist on')
                        else:
                            rcon.command('whitelist off')
                    except:
                        pass
                    finally:
                        try:
                            rcon.disconnect()
                        except:
                            pass
        
        # Escribir archivo modificado
        with open(server_properties_path, 'w') as f:
            f.write(content)
        
        print(f"✅ server.properties actualizado para {server.name}")
    
    # Log de cambios
    print(f"Aplicando settings para servidor {server.name}:")
    print(f"  - is_public: {server.is_public}")
    print(f"  - auth_mode: {server.auth_mode}")
    print(f"  - enable_whitelist: {server.enable_whitelist}")
    print(f"  - online_mode: {server.online_mode}")
    if data:
        if 'max_players' in data:
            print(f"  - max_players: {data['max_players']}")
        if 'motd' in data:
            print(f"  - motd: {data['motd']}")

@login_required
@require_server_permission('manage_users')
@require_http_methods(["GET"])
def minecraft_users_list(request, server_id):
    """Listar usuarios de Minecraft en base de datos"""
    server = request.server
    
    if server.auth_mode not in ['database', 'both']:
        return JsonResponse({
            'success': False,
            'error': 'Server does not use database authentication'
        }, status=400)
    
    users = MinecraftUser.objects.filter(server=server).values(
        'id', 'username', 'is_active', 'last_login', 'created_at'
    )
    
    return JsonResponse({
        'success': True,
        'data': list(users)
    })

@login_required
@require_server_permission('manage_users')
@require_http_methods(["POST"])
def minecraft_user_create(request, server_id):
    """Crear usuario de Minecraft"""
    server = request.server
    
    if server.auth_mode not in ['database', 'both']:
        return JsonResponse({
            'success': False,
            'error': 'Server does not use database authentication'
        }, status=400)
    
    data = json.loads(request.body)
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or len(username) < 3:
        return JsonResponse({
            'success': False,
            'error': 'Username must be at least 3 characters'
        }, status=400)
    
    if not password or len(password) < 6:
        return JsonResponse({
            'success': False,
            'error': 'Password must be at least 6 characters'
        }, status=400)
    
    if MinecraftUser.objects.filter(server=server, username=username).exists():
        return JsonResponse({
            'success': False,
            'error': 'Username already exists'
        }, status=400)
    
    user = MinecraftUser(server=server, username=username)
    user.set_password(password)
    user.save()
    
    return JsonResponse({
        'success': True,
        'message': f'User {username} created',
        'data': {
            'id': user.id,
            'username': user.username,
            'is_active': user.is_active,
        }
    })

@login_required
@require_server_permission('manage_users')
@require_http_methods(["POST"])
def minecraft_user_update(request, server_id, user_id):
    """Actualizar usuario de Minecraft"""
    server = request.server
    
    try:
        user = MinecraftUser.objects.get(id=user_id, server=server)
    except MinecraftUser.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'User not found'
        }, status=404)
    
    data = json.loads(request.body)
    
    if 'password' in data and data['password']:
        if len(data['password']) < 6:
            return JsonResponse({
                'success': False,
                'error': 'Password must be at least 6 characters'
            }, status=400)
        user.set_password(data['password'])
    
    if 'is_active' in data:
        user.is_active = data['is_active']
    
    user.save()
    
    return JsonResponse({
        'success': True,
        'message': f'User {user.username} updated',
        'data': {
            'id': user.id,
            'username': user.username,
            'is_active': user.is_active,
        }
    })

@login_required
@require_server_permission('manage_users')
@require_http_methods(["DELETE"])
def minecraft_user_delete(request, server_id, user_id):
    """Eliminar usuario de Minecraft"""
    server = request.server
    
    try:
        user = MinecraftUser.objects.get(id=user_id, server=server)
        username = user.username
        user.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'User {username} deleted'
        })
    except MinecraftUser.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'User not found'
        }, status=404)

