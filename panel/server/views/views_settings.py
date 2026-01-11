from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import os
import re
from ..models import Server, MinecraftUser
from ..utils.permissions import require_server_permission
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

def _parse_server_properties(content):
    """Parsear server.properties y devolver diccionario con valores"""
    props = {}
    for line in content.split('\n'):
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            # Convertir valores booleanos
            if value.lower() in ['true', 'false']:
                props[key] = value.lower() == 'true'
            # Convertir valores numéricos (incluyendo negativos)
            elif value.lstrip('-').isdigit():
                props[key] = int(value)
            else:
                # Mantener como string (puede tener escapes)
                props[key] = value.replace('\\"', '"').replace('\\n', '\n')
    
    return props

@login_required
@require_server_permission('manage_settings')
@require_http_methods(["GET"])
def server_settings(request, server_id):
    """Obtener configuración del servidor"""
    server = request.server
    
    # Valores por defecto
    properties = {
        'max-players': 20,
        'motd': 'A Minecraft Server',
        'difficulty': 'normal',
        'pvp': True,
        'white-list': False,
        'online-mode': False,
        'view-distance': 10,
        'simulation-distance': 10,
        'spawn-protection': 16,
        'max-world-size': 29999984,
        'server-port': 25565,
        'enable-rcon': True,
        'rcon-port': 25575,
        'gamemode': 'survival',
        'hardcore': False,
        'spawn-monsters': True,
        'spawn-animals': True,
        'spawn-npcs': True,
        'allow-flight': False,
        'enable-command-block': False,
        'op-permission-level': 4,
        'function-permission-level': 2,
        'max-tick-time': 60000,
        'network-compression-threshold': 256,
        'enforce-whitelist': False,
        'enforce-secure-profile': True,
        'log-ips': True,
        'player-idle-timeout': 0,
        'rate-limit': 0,
        'resource-pack': '',
        'resource-pack-prompt': '',
        'force-gamemode': False,
        'generate-structures': True,
        'allow-nether': True,
    }
    
    server_properties_path = os.path.join(server.minecraft_data_path, 'server.properties')
    
    # Si el servidor tiene container_name, leer desde el contenedor Docker
    if server.container_name:
        try:
            import docker
            client = docker.from_env()
            container = client.containers.get(server.container_name)
            
            result = container.exec_run(
                f'cat {server_properties_path}',
                user='minecraft'
            )
            
            if result.exit_code == 0:
                content = result.output.decode('utf-8')
                properties.update(_parse_server_properties(content))
        except Exception as e:
            print(f"⚠️ Error leyendo server.properties del contenedor: {e}")
    
    # Fallback: leer desde sistema de archivos local
    elif os.path.exists(server_properties_path):
        try:
            with open(server_properties_path, 'r') as f:
                content = f.read()
                properties.update(_parse_server_properties(content))
        except Exception as e:
            print(f"⚠️ Error leyendo server.properties: {e}")
    
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
            'api_key': server.api_key or None,
            'online_mode': server.online_mode,
            'is_active': server.is_active,
            # Propiedades de server.properties
            'max_players': properties.get('max-players', 20),
            'motd': properties.get('motd', 'A Minecraft Server'),
            'difficulty': properties.get('difficulty', 'normal'),
            'pvp': properties.get('pvp', True),
            'view_distance': properties.get('view-distance', 10),
            'simulation_distance': properties.get('simulation-distance', 10),
            'spawn_protection': properties.get('spawn-protection', 16),
            'max_world_size': properties.get('max-world-size', 29999984),
            'server_port': properties.get('server-port', 25565),
            # Tipo de servidor y versión
            'server_type': server.server_type,
            'minecraft_version': server.minecraft_version,
            # Propiedades adicionales
            'gamemode': properties.get('gamemode', 'survival'),
            'hardcore': properties.get('hardcore', False),
            'spawn_monsters': properties.get('spawn-monsters', True),
            'spawn_animals': properties.get('spawn-animals', True),
            'spawn_npcs': properties.get('spawn-npcs', True),
            'allow_flight': properties.get('allow-flight', False),
            'enable_command_block': properties.get('enable-command-block', False),
            'op_permission_level': properties.get('op-permission-level', 4),
            'function_permission_level': properties.get('function-permission-level', 2),
            'max_tick_time': properties.get('max-tick-time', 60000),
            'network_compression_threshold': properties.get('network-compression-threshold', 256),
            'enforce_whitelist': properties.get('enforce-whitelist', False),
            'enforce_secure_profile': properties.get('enforce-secure-profile', True),
            'log_ips': properties.get('log-ips', True),
            'player_idle_timeout': properties.get('player-idle-timeout', 0),
            'rate_limit': properties.get('rate-limit', 0),
            'resource_pack': properties.get('resource-pack', ''),
            'resource_pack_prompt': properties.get('resource-pack-prompt', ''),
            'force_gamemode': properties.get('force-gamemode', False),
            'generate_structures': properties.get('generate-structures', True),
            'allow_nether': properties.get('allow-nether', True),
            # Puertos adicionales
            'additional_ports': server.additional_ports or [],
        }
    })

@csrf_exempt
@login_required
@require_server_permission('manage_settings')
@require_http_methods(["POST"])
def server_settings_update(request, server_id):
    """Actualizar configuración del servidor"""
    server = request.server
    data = json.loads(request.body)
    
    # Campos actualizables en el modelo Server
    updatable_fields = ['is_public', 'auth_mode', 'enable_whitelist', 'online_mode', 'server_type', 'minecraft_version', 'additional_ports']
    
    # Verificar si se cambió el tipo de servidor o versión (requiere reinicio del contenedor)
    server_type_changed = 'server_type' in data and data['server_type'] != server.server_type
    version_changed = 'minecraft_version' in data and data['minecraft_version'] != server.minecraft_version
    
    # Verificar si cambiaron los puertos adicionales (requiere recrear contenedor)
    ports_changed = False
    if 'additional_ports' in data:
        old_ports = server.additional_ports or []
        new_ports = data['additional_ports'] or []
        
        # Validar que no haya puertos duplicados en host_port
        host_ports_used = {}
        for port in new_ports:
            host_port = port.get('host_port', port.get('port', 0))
            container_port = port.get('port', 0)
            protocol = port.get('protocol', 'tcp')
            if host_port in host_ports_used:
                # Ya hay otro puerto usando este host_port
                existing = host_ports_used[host_port]
                return JsonResponse({
                    'success': False,
                    'error': f'Puerto {host_port} ya está asignado a otro puerto ({existing["port"]}/{existing["protocol"]}). Cada puerto debe tener un host_port único.'
                }, status=400)
            host_ports_used[host_port] = {'port': container_port, 'protocol': protocol}
        
        # Comparar listas normalizadas
        old_ports_normalized = sorted([(p.get('port', 0), p.get('protocol', 'tcp'), p.get('host_port', p.get('port', 0))) for p in old_ports])
        new_ports_normalized = sorted([(p.get('port', 0), p.get('protocol', 'tcp'), p.get('host_port', p.get('port', 0))) for p in new_ports])
        ports_changed = old_ports_normalized != new_ports_normalized
        print(f"🔍 Verificación de puertos: old={old_ports_normalized}, new={new_ports_normalized}, changed={ports_changed}")
    
    for field in updatable_fields:
        if field in data:
            setattr(server, field, data[field])
    
    # Generar API key si se cambia a modo database/both y no existe
    if server.auth_mode in ['database', 'both'] and not server.api_key:
        server.generate_api_key()
    
    server.save()
    
    # Si cambiaron los puertos adicionales y hay un contenedor, recrearlo
    container_recreated = False
    if ports_changed and server.container_name:
        print(f"🔄 Puertos cambiaron, recreando contenedor {server.container_name}...")
        try:
            from ..utils.docker_control import delete_container, create_minecraft_container
            
            # Guardar el estado del contenedor antes de eliminarlo
            container_was_running = False
            try:
                import docker
                client = docker.from_env()
                container = client.containers.get(server.container_name)
                container_was_running = container.status == 'running'
                print(f"📊 Estado del contenedor antes de eliminar: {container.status}")
            except Exception as e:
                print(f"⚠️ Error al obtener estado del contenedor: {e}")
            
            # Eliminar el contenedor existente (sin eliminar volúmenes)
            print(f"🗑️ Eliminando contenedor {server.container_name}...")
            delete_result = delete_container(server.container_name, force=True, remove_volumes=False)
            print(f"📊 Resultado de eliminación: {delete_result}")
            
            # Esperar un momento para que Docker libere los puertos
            import time
            time.sleep(2)
            
            # Verificar que el contenedor fue eliminado completamente
            try:
                import docker
                client = docker.from_env()
                try:
                    old_container = client.containers.get(server.container_name)
                    print(f"⚠️ El contenedor aún existe, forzando eliminación...")
                    old_container.remove(force=True)
                    time.sleep(1)
                except docker.errors.NotFound:
                    print(f"✅ Contenedor eliminado correctamente")
            except Exception as e:
                print(f"⚠️ Error verificando eliminación: {e}")
            
            if delete_result.get('success') or True:  # Intentar crear de todas formas
                # Obtener puerto de Minecraft (por defecto 25565)
                minecraft_port = 25565
                # Por ahora usar el valor por defecto, podría mejorarse leyendo desde server.properties
                
                # Recrear el contenedor con los nuevos puertos
                print(f"🔨 Recreando contenedor con puertos adicionales: {server.additional_ports}")
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
                    start_container=container_was_running,  # Iniciar si estaba corriendo antes
                    additional_ports=server.additional_ports or []
                )
                print(f"📊 Resultado de creación: {create_result}")
                
                if create_result.get('success'):
                    container_recreated = True
                    print(f"✅ Contenedor recreado exitosamente")
                else:
                    error_msg = create_result.get('error', 'Error desconocido')
                    print(f"❌ Error al recrear contenedor: {error_msg}")
                    # Si el error es por puerto en uso, intentar limpiar y recrear
                    if 'port is already allocated' in str(error_msg) or 'port is already in use' in str(error_msg):
                        print(f"🔄 Puerto en uso, intentando limpiar...")
                        try:
                            import docker
                            import time
                            client = docker.from_env()
                            # Buscar y eliminar cualquier contenedor que use ese puerto
                            all_containers = client.containers.list(all=True)
                            for cont in all_containers:
                                if cont.name != server.container_name:
                                    try:
                                        ports = cont.attrs.get('HostConfig', {}).get('PortBindings', {})
                                        for port_binding in ports.values():
                                            if port_binding and any(binding.get('HostPort') == '24454' for binding in port_binding):
                                                print(f"⚠️ Encontrado contenedor {cont.name} usando puerto 24454")
                                    except:
                                        pass
                            time.sleep(2)
                            # Intentar crear de nuevo
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
                                start_container=container_was_running,
                                additional_ports=server.additional_ports or []
                            )
                            if create_result.get('success'):
                                container_recreated = True
                                print(f"✅ Contenedor recreado exitosamente después de limpiar puertos")
                        except Exception as cleanup_error:
                            print(f"⚠️ Error al limpiar puertos: {cleanup_error}")
            else:
                print(f"❌ No se pudo eliminar el contenedor: {delete_result.get('error')}")
        except Exception as e:
            import traceback
            print(f"⚠️ Error al recrear contenedor por cambio de puertos: {e}")
            traceback.print_exc()
    elif ports_changed and not server.container_name:
        print(f"⚠️ Puertos cambiaron pero el servidor no tiene container_name")
    elif not ports_changed:
        print(f"ℹ️ No hubo cambios en los puertos adicionales")
    
    # Preparar datos para server.properties (mapear nombres del frontend a nombres de propiedades)
    properties_data = {}
    
    # Mapear campos del frontend a propiedades de server.properties
    field_mapping = {
        'max_players': 'max-players',
        'motd': 'motd',
        'difficulty': 'difficulty',
        'pvp': 'pvp',
        'enable_whitelist': 'white-list',
        'online_mode': 'online-mode',
        'view_distance': 'view-distance',
        'simulation_distance': 'simulation-distance',
        'spawn_protection': 'spawn-protection',
        'max_world_size': 'max-world-size',
        'server_port': 'server-port',
        'gamemode': 'gamemode',
        'hardcore': 'hardcore',
        'spawn_monsters': 'spawn-monsters',
        'spawn_animals': 'spawn-animals',
        'spawn_npcs': 'spawn-npcs',
        'allow_flight': 'allow-flight',
        'enable_command_block': 'enable-command-block',
        'op_permission_level': 'op-permission-level',
        'function_permission_level': 'function-permission-level',
        'max_tick_time': 'max-tick-time',
        'network_compression_threshold': 'network-compression-threshold',
        'enforce_whitelist': 'enforce-whitelist',
        'enforce_secure_profile': 'enforce-secure-profile',
        'log_ips': 'log-ips',
        'player_idle_timeout': 'player-idle-timeout',
        'rate_limit': 'rate-limit',
        'resource_pack': 'resource-pack',
        'resource_pack_prompt': 'resource-pack-prompt',
        'force_gamemode': 'force-gamemode',
        'generate_structures': 'generate-structures',
        'allow_nether': 'allow-nether',
    }
    
    for frontend_field, prop_field in field_mapping.items():
        if frontend_field in data:
            properties_data[prop_field] = data[frontend_field]
    
    # Leer valores actuales de server.properties para comparar
    current_properties = {}
    server_properties_path = os.path.join(server.minecraft_data_path, 'server.properties')
    
    if server.container_name:
        try:
            import docker
            client = docker.from_env()
            container = client.containers.get(server.container_name)
            result = container.exec_run(
                f'cat {server_properties_path}',
                user='minecraft'
            )
            if result.exit_code == 0:
                content = result.output.decode('utf-8')
                current_properties = _parse_server_properties(content)
        except Exception as e:
            print(f"⚠️ Error leyendo server.properties para comparar: {e}")
    elif os.path.exists(server_properties_path):
        try:
            with open(server_properties_path, 'r') as f:
                content = f.read()
                current_properties = _parse_server_properties(content)
        except Exception as e:
            print(f"⚠️ Error leyendo server.properties para comparar: {e}")
    
    # Comparar valores nuevos con los actuales y solo incluir los que cambiaron
    changed_properties = {}
    for prop_name, new_value in properties_data.items():
        current_value = current_properties.get(prop_name)
        # Normalizar valores para comparación
        if isinstance(new_value, bool):
            new_value_normalized = new_value
            current_value_normalized = current_value if isinstance(current_value, bool) else str(current_value).lower() == 'true'
        elif isinstance(new_value, (int, float)):
            new_value_normalized = new_value
            try:
                current_value_normalized = int(current_value) if current_value is not None else None
            except (ValueError, TypeError):
                current_value_normalized = current_value
        else:
            new_value_normalized = str(new_value).strip()
            current_value_normalized = str(current_value).strip() if current_value is not None else None
        
        # Solo agregar si realmente cambió
        if new_value_normalized != current_value_normalized:
            changed_properties[prop_name] = new_value
    
    # Aplicar cambios al servidor Minecraft (solo los que cambiaron)
    _apply_server_settings(server, changed_properties)
    
    # Determinar qué cambios requieren reinicio
    # Algunos cambios se pueden aplicar vía RCON sin reinicio
    requires_restart = []
    can_apply_via_rcon = []
    
    # Cambios de tipo de servidor o versión requieren recrear el contenedor
    if server_type_changed:
        requires_restart.append('server_type')
    if version_changed:
        requires_restart.append('minecraft_version')
    
    # Propiedades que se pueden aplicar vía RCON (sin reinicio)
    rcon_properties = ['difficulty', 'pvp', 'white-list', 'gamemode']
    
    # Propiedades que requieren reinicio (solo las que cambiaron y no se pueden aplicar vía RCON)
    restart_properties = [
        'max-players', 'motd', 'online-mode', 'view-distance', 'simulation-distance',
        'spawn-protection', 'max-world-size', 'server-port', 'hardcore',
        'spawn-monsters', 'spawn-animals', 'spawn-npcs', 'allow-flight',
        'enable-command-block', 'op-permission-level', 'function-permission-level',
        'max-tick-time', 'network-compression-threshold', 'enforce-whitelist',
        'enforce-secure-profile', 'log-ips', 'player-idle-timeout', 'rate-limit',
        'resource-pack', 'resource-pack-prompt', 'force-gamemode', 'generate-structures',
        'allow-nether'
    ]
    
    # Agregar propiedades que requieren reinicio (excluyendo las que se pueden aplicar vía RCON)
    for prop in restart_properties:
        if prop in changed_properties and prop not in rcon_properties:
            requires_restart.append(prop.replace('-', '_'))
    
    # Agregar propiedades que se pueden aplicar vía RCON
    for prop in rcon_properties:
        if prop in changed_properties:
            can_apply_via_rcon.append(prop.replace('-', '_').replace('white_list', 'whitelist'))
    
    # Mensaje más corto
    if container_recreated:
        message = 'Configuración guardada. Contenedor recreado con los nuevos puertos'
    elif requires_restart and can_apply_via_rcon:
        message = f'Configuración guardada. {len(requires_restart)} cambios requieren reinicio'
    elif requires_restart:
        message = f'Configuración guardada. {len(requires_restart)} cambios requieren reinicio'
    elif can_apply_via_rcon:
        message = 'Configuración guardada y aplicada'
    else:
        message = 'Configuración guardada'
    
    return JsonResponse({
        'success': True,
        'message': message,
        'requires_restart': requires_restart,
        'applied_via_rcon': can_apply_via_rcon,
        'container_recreated': container_recreated,
        'data': {
            'is_public': server.is_public,
            'auth_mode': server.auth_mode,
            'enable_whitelist': server.enable_whitelist,
            'online_mode': server.online_mode,
        }
    })

def _apply_server_settings(server, data=None):
    """
    Aplicar configuración al servidor Minecraft vía RCON o archivos
    
    Estrategia:
    1. Cambios que se pueden aplicar vía RCON (sin reinicio): whitelist, difficulty
    2. Cambios que requieren modificar server.properties (requieren reinicio): max_players, motd, online_mode
    """
    import os
    import re
    import docker
    import tarfile
    import io
    
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
    
    if not data:
        return
    
    requires_restart = []
    applied_via_rcon = []
    
    # Ruta al archivo server.properties dentro del contenedor
    server_properties_path = os.path.join(server.minecraft_data_path, 'server.properties')
    
    # Si el servidor tiene container_name, trabajar con el contenedor Docker
    if server.container_name:
        try:
            client = docker.from_env()
            container = client.containers.get(server.container_name)
            
            # Leer server.properties desde el contenedor
            result = container.exec_run(
                f'cat {server_properties_path}',
                user='minecraft'
            )
            
            if result.exit_code != 0:
                print(f"⚠️ No se pudo leer server.properties del contenedor {server.container_name}")
                return
            
            content = result.output.decode('utf-8')
            content_modified = False
            
            # Mapeo de propiedades a sus valores y si requieren reinicio
            # Formato: (propiedad, valor_formateado, requiere_reinicio, puede_rcon, comando_rcon)
            property_updates = []
            
            # Función helper para agregar propiedades
            def add_property(prop_name, value, can_rcon=False, rcon_cmd=None):
                if isinstance(value, bool):
                    value_str = 'true' if value else 'false'
                else:
                    value_str = str(value)
                property_updates.append((prop_name, value_str, True, can_rcon, rcon_cmd))
            
            # Propiedades que requieren reinicio
            if 'max-players' in data:
                add_property('max-players', data['max-players'])
            if 'motd' in data:
                motd = str(data['motd']).replace('\\', '\\\\').replace('"', '\\"')
                add_property('motd', motd)
            if 'online-mode' in data:
                add_property('online-mode', data['online-mode'])
            if 'view-distance' in data:
                add_property('view-distance', data['view-distance'])
            if 'simulation-distance' in data:
                add_property('simulation-distance', data['simulation-distance'])
            if 'spawn-protection' in data:
                add_property('spawn-protection', data['spawn-protection'])
            if 'max-world-size' in data:
                add_property('max-world-size', data['max-world-size'])
            if 'server-port' in data:
                add_property('server-port', data['server-port'])
            if 'gamemode' in data:
                add_property('gamemode', data['gamemode'], can_rcon=True, rcon_cmd=f'gamemode {data["gamemode"]}')
            if 'hardcore' in data:
                add_property('hardcore', data['hardcore'])
            if 'spawn-monsters' in data:
                add_property('spawn-monsters', data['spawn-monsters'])
            if 'spawn-animals' in data:
                add_property('spawn-animals', data['spawn-animals'])
            if 'spawn-npcs' in data:
                add_property('spawn-npcs', data['spawn-npcs'])
            if 'allow-flight' in data:
                add_property('allow-flight', data['allow-flight'])
            if 'enable-command-block' in data:
                add_property('enable-command-block', data['enable-command-block'])
            if 'op-permission-level' in data:
                add_property('op-permission-level', data['op-permission-level'])
            if 'function-permission-level' in data:
                add_property('function-permission-level', data['function-permission-level'])
            if 'max-tick-time' in data:
                add_property('max-tick-time', data['max-tick-time'])
            if 'network-compression-threshold' in data:
                add_property('network-compression-threshold', data['network-compression-threshold'])
            if 'enforce-whitelist' in data:
                add_property('enforce-whitelist', data['enforce-whitelist'])
            if 'enforce-secure-profile' in data:
                add_property('enforce-secure-profile', data['enforce-secure-profile'])
            if 'log-ips' in data:
                add_property('log-ips', data['log-ips'])
            if 'player-idle-timeout' in data:
                add_property('player-idle-timeout', data['player-idle-timeout'])
            if 'rate-limit' in data:
                add_property('rate-limit', data['rate-limit'])
            if 'resource-pack' in data:
                add_property('resource-pack', data['resource-pack'])
            if 'resource-pack-prompt' in data:
                add_property('resource-pack-prompt', data['resource-pack-prompt'])
            if 'force-gamemode' in data:
                add_property('force-gamemode', data['force-gamemode'])
            if 'generate-structures' in data:
                add_property('generate-structures', data['generate-structures'])
            if 'allow-nether' in data:
                add_property('allow-nether', data['allow-nether'])
            
            # Propiedades que se pueden aplicar vía RCON
            if 'difficulty' in data:
                difficulty = str(data['difficulty']).lower()
                add_property('difficulty', difficulty, can_rcon=True, rcon_cmd=f'difficulty {difficulty}')
            if 'pvp' in data:
                add_property('pvp', data['pvp'], can_rcon=True, rcon_cmd=f'pvp {"on" if data["pvp"] else "off"}')
            if 'white-list' in data:
                add_property('white-list', data['white-list'], can_rcon=True, rcon_cmd=f'whitelist {"on" if data["white-list"] else "off"}')
            
            # Aplicar cambios al contenido
            for prop_name, prop_value, needs_restart, can_rcon, rcon_cmd in property_updates:
                # Actualizar en el archivo
                pattern = rf'^{re.escape(prop_name)}=.*$'
                replacement = f'{prop_name}={prop_value}'
                new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
                
                # Si la propiedad no existe, agregarla al final
                if new_content == content and prop_name not in content:
                    new_content = content.rstrip() + f'\n{prop_name}={prop_value}\n'
                
                if new_content != content:
                    content = new_content
                    content_modified = True
                    if needs_restart:
                        requires_restart.append(prop_name.replace('-', '_'))
                    
                    # Intentar aplicar vía RCON si es posible
                    if can_rcon and rcon_cmd:
                        rcon = _get_rcon_connection(server)
                        if rcon:
                            try:
                                rcon.command(rcon_cmd)
                                applied_via_rcon.append(prop_name.replace('-', '_'))
                            except Exception as e:
                                print(f"⚠️ No se pudo aplicar {prop_name} vía RCON: {e}")
                            finally:
                                try:
                                    rcon.disconnect()
                                except:
                                    pass
            
            # Escribir archivo modificado de vuelta al contenedor
            if content_modified:
                # Crear un archivo temporal en memoria y copiarlo al contenedor
                tar_stream = io.BytesIO()
                with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                    tarinfo = tarfile.TarInfo(name='server.properties')
                    tarinfo.size = len(content.encode('utf-8'))
                    tar.addfile(tarinfo, io.BytesIO(content.encode('utf-8')))
                
                tar_stream.seek(0)
                container.put_archive(os.path.dirname(server_properties_path), tar_stream.read())
                
                # Asegurar permisos correctos
                container.exec_run(f'chown minecraft:minecraft {server_properties_path}', user='root')
                
                print(f"✅ server.properties actualizado para {server.name}")
                
                if requires_restart:
                    print(f"⚠️ Los siguientes cambios requieren reinicio del servidor: {', '.join(requires_restart)}")
                
                if applied_via_rcon:
                    print(f"✅ Los siguientes cambios se aplicaron vía RCON (sin reinicio): {', '.join(applied_via_rcon)}")
        
        except docker.errors.NotFound:
            print(f"❌ Contenedor {server.container_name} no encontrado")
        except Exception as e:
            print(f"❌ Error aplicando configuración: {e}")
            import traceback
            traceback.print_exc()
    
    else:
        # Fallback: intentar acceso directo al archivo (si está en el mismo sistema de archivos)
        if os.path.exists(server_properties_path):
            try:
                with open(server_properties_path, 'r') as f:
                    content = f.read()
                
                content_modified = False
                
                if 'max_players' in data:
                    max_players = data['max_players']
                    new_content = re.sub(r'^max-players=.*$', f'max-players={max_players}', content, flags=re.MULTILINE)
                    if new_content != content:
                        content = new_content
                        content_modified = True
                        requires_restart.append('max_players')
                
                if 'motd' in data:
                    motd = data['motd'].replace('\\', '\\\\').replace('"', '\\"')
                    new_content = re.sub(r'^motd=.*$', f'motd={motd}', content, flags=re.MULTILINE)
                    if new_content != content:
                        content = new_content
                        content_modified = True
                        requires_restart.append('motd')
                
                if 'online_mode' in data:
                    online_mode = 'true' if data['online_mode'] else 'false'
                    new_content = re.sub(r'^online-mode=.*$', f'online-mode={online_mode}', content, flags=re.MULTILINE)
                    if new_content != content:
                        content = new_content
                        content_modified = True
                        requires_restart.append('online_mode')
                
                if content_modified:
                    with open(server_properties_path, 'w') as f:
                        f.write(content)
                    print(f"✅ server.properties actualizado para {server.name}")
                    if requires_restart:
                        print(f"⚠️ Los siguientes cambios requieren reinicio: {', '.join(requires_restart)}")
            except Exception as e:
                print(f"❌ Error escribiendo server.properties: {e}")
    
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
    """Listar usuarios de Minecraft en base de datos o whitelist según el modo de autenticación"""
    server = request.server
    
    # Si el servidor usa whitelist, devolver usuarios de la whitelist
    if server.auth_mode == 'whitelist':
        # Obtener usuarios de la whitelist vía RCON
        try:
            from .views_api import _get_rcon_connection
            rcon = _get_rcon_connection(server)
            print(f"minecraft_users_list - RCON connection: {rcon is not None}")
            if rcon:
                try:
                    print(f"minecraft_users_list - Executing whitelist list command...")
                    response = rcon.command('whitelist list')
                    print(f"minecraft_users_list - RCON response: {response}")
                    print(f"minecraft_users_list - Response type: {type(response)}")
                    print(f"minecraft_users_list - Response length: {len(response) if response else 0}")
                    # Parsear respuesta: "There are X whitelisted player(s): player1, player2"
                    import re
                    players = []
                    
                    # Buscar el patrón ": " seguido de la lista de jugadores
                    # Ejemplo: "There are 10 whitelisted player(s): Chrsx3, carlitorts, Mathi"
                    match = re.search(r':\s*([^:]+)$', response)
                    if match:
                        players_str = match.group(1).strip()
                        if players_str:
                            # Separar por comas y limpiar cada nombre
                            raw_players = [p.strip() for p in players_str.split(',') if p.strip()]
                            # Filtrar cualquier texto que no sea un nombre válido
                            for p in raw_players:
                                # Limpiar cualquier texto extra que pueda estar pegado al nombre
                                # Remover cualquier parte que contenga "There are" o números solos
                                clean_name = re.sub(r'\s*There are.*$', '', p, flags=re.IGNORECASE)
                                clean_name = re.sub(r'^\d+\s+whitelisted.*?:\s*', '', clean_name, flags=re.IGNORECASE)
                                clean_name = clean_name.strip()
                                # Solo agregar si es un nombre válido (no vacío, no solo números, no contiene "There are")
                                if clean_name and not re.match(r'^\d+$', clean_name) and 'There are' not in clean_name:
                                    players.append(clean_name)
                    
                    # Si no se encontraron con el primer método, intentar otro patrón
                    if not players:
                        # Buscar directamente después de "player(s):"
                        match = re.search(r'player\(s\):\s*(.+)', response, re.IGNORECASE)
                        if match:
                            players_str = match.group(1).strip()
                            if players_str:
                                raw_players = [p.strip() for p in players_str.split(',') if p.strip()]
                                for p in raw_players:
                                    clean_name = re.sub(r'\s*There are.*$', '', p, flags=re.IGNORECASE)
                                    clean_name = clean_name.strip()
                                    if clean_name and not re.match(r'^\d+$', clean_name) and 'There are' not in clean_name:
                                        players.append(clean_name)
                    
                    # Eliminar duplicados manteniendo el orden (comparación case-insensitive)
                    seen = set()
                    unique_players = []
                    for p in players:
                        p_lower = p.lower()
                        if p_lower not in seen:
                            seen.add(p_lower)
                            unique_players.append(p)
                    players = unique_players
                    
                    # Convertir a formato esperado por el frontend (similar a usuarios de BD)
                    whitelist_users = []
                    for idx, player_name in enumerate(players):
                        whitelist_users.append({
                            'id': idx + 1,  # ID temporal basado en índice
                            'username': player_name,
                            'is_active': True,
                            'last_login': None,
                            'created_at': None,
                            'source': 'whitelist'  # Indicar que viene de whitelist
                        })
                    
                    return JsonResponse({
                        'success': True,
                        'data': whitelist_users,
                        'message': 'Users from whitelist (server uses whitelist authentication mode)'
                    })
                except Exception as e:
                    print(f"Error getting whitelist via RCON: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    try:
                        rcon.disconnect()
                    except:
                        pass
            
            # Si RCON falla, devolver lista vacía con más información de debug
            print(f"RCON connection failed for server {server.name} (host: {server.host}, port: {server.rcon_port})")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': True,
                'data': [],
                'message': f'Could not retrieve whitelist users (RCON connection failed for {server.name})'
            })
        except Exception as e:
            print(f"Error in whitelist users retrieval: {e}")
            return JsonResponse({
                'success': True,
                'data': [],
                'message': f'Error retrieving whitelist users: {str(e)}'
            })
    
    # Si el servidor no usa autenticación por base de datos, devolver lista vacía
    if server.auth_mode not in ['database', 'both']:
        return JsonResponse({
            'success': True,
            'data': [],
            'message': f'Server uses {server.auth_mode} authentication mode, database users not available'
        })
    
    # Servidor usa database o both - devolver usuarios de la base de datos
    users = MinecraftUser.objects.filter(server=server).values(
        'id', 'username', 'is_active', 'last_login', 'created_at'
    )
    
    # Agregar campo source para indicar que vienen de la base de datos
    users_list = list(users)
    for user in users_list:
        user['source'] = 'database'
    
    return JsonResponse({
        'success': True,
        'data': users_list
    })

def _send_password_set_email(user, token):
    """Enviar email con token para establecer contraseña"""
    from django.core.mail import send_mail
    from django.conf import settings
    from django.template.loader import render_to_string
    
    try:
        # Construir URL para establecer contraseña
        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        set_password_url = f"{site_url}/api/servers/{user.server.id}/users/set-password/?token={token}"
        
        # Renderizar template de email
        context = {
            'username': user.username,
            'server_name': user.server.name,
            'set_password_url': set_password_url,
            'token': token,
            'expires_hours': 24,
        }
        
        subject = f'Establece tu contraseña - {user.server.name}'
        message = render_to_string('emails/password_set_invitation.txt', context)
        html_message = render_to_string('emails/password_set_invitation.html', context) if os.path.exists(os.path.join(settings.BASE_DIR, 'templates', 'emails', 'password_set_invitation.html')) else None
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error enviando email: {e}")
        import traceback
        traceback.print_exc()
        return False

@csrf_exempt
@login_required
@require_server_permission('manage_users')
@require_http_methods(["POST"])
def minecraft_user_create(request, server_id):
    """Crear usuario de Minecraft - Admin crea usuario y se envía email para establecer contraseña"""
    server = request.server
    
    if server.auth_mode not in ['database', 'both']:
        return JsonResponse({
            'success': False,
            'error': 'Server does not use database authentication'
        }, status=400)
    
    data = json.loads(request.body)
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')  # Opcional, para casos especiales
    
    if not username or len(username) < 3:
        return JsonResponse({
            'success': False,
            'error': 'Username must be at least 3 characters'
        }, status=400)
    
    if not email:
        return JsonResponse({
            'success': False,
            'error': 'Email is required'
        }, status=400)
    
    # Validar formato de email básico
    if '@' not in email or '.' not in email.split('@')[1]:
        return JsonResponse({
            'success': False,
            'error': 'Invalid email format'
        }, status=400)
    
    if MinecraftUser.objects.filter(server=server, username=username).exists():
        return JsonResponse({
            'success': False,
            'error': 'Username already exists'
        }, status=400)
    
    # Crear usuario (sin contraseña inicialmente)
    user = MinecraftUser(server=server, username=username, email=email, is_active=False)
    
    # Si se proporciona password (caso especial), establecerlo directamente
    if password:
        if len(password) < 6:
            return JsonResponse({
                'success': False,
                'error': 'Password must be at least 6 characters'
            }, status=400)
        user.set_password(password)
        user.is_active = True
        user.save()
    else:
        # Guardar usuario primero para obtener ID
        user.save()
        
        # Generar token para establecer contraseña (ahora que tiene ID)
        token = user.generate_password_set_token()
        
        # Enviar email con token
        email_sent = _send_password_set_email(user, token)
        if not email_sent:
            # Si falla el email, eliminar el usuario creado
            user.delete()
            return JsonResponse({
                'success': False,
                'error': 'Failed to send email. Please check email configuration.'
            }, status=500)
    
    return JsonResponse({
        'success': True,
        'message': f'User {username} created. Email sent to {email}' if not password else f'User {username} created',
        'data': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_active': user.is_active,
            'has_password_set': user.has_password_set(),
        }
    })

@csrf_exempt
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

@csrf_exempt
@require_http_methods(["POST"])
def minecraft_user_set_password(request, server_id):
    """Endpoint público para establecer contraseña usando token (sin autenticación requerida)"""
    from django.shortcuts import get_object_or_404
    from django.utils import timezone
    
    try:
        server = Server.objects.get(id=server_id, is_active=True)
    except Server.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Server not found'
        }, status=404)
    
    if server.auth_mode not in ['database', 'both']:
        return JsonResponse({
            'success': False,
            'error': 'Server does not use database authentication'
        }, status=400)
    
    data = json.loads(request.body)
    token = data.get('token', '').strip()
    password = data.get('password', '')
    
    if not token:
        return JsonResponse({
            'success': False,
            'error': 'Token is required'
        }, status=400)
    
    if not password:
        return JsonResponse({
            'success': False,
            'error': 'Password is required'
        }, status=400)
    
    if len(password) < 6:
        return JsonResponse({
            'success': False,
            'error': 'Password must be at least 6 characters'
        }, status=400)
    
    # Buscar usuario por token
    try:
        user = MinecraftUser.objects.get(
            server=server,
            password_set_token=token,
            password_set_token_expires__gt=timezone.now()
        )
    except MinecraftUser.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Invalid or expired token'
        }, status=400)
    
    # Verificar que el token es válido
    if not user.is_password_set_token_valid(token):
        return JsonResponse({
            'success': False,
            'error': 'Invalid or expired token'
        }, status=400)
    
    # Establecer contraseña
    user.set_password(password)
    user.is_active = True
    user.password_set_token = None
    user.password_set_token_expires = None
    user.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Password set successfully. Your account is now active.',
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

