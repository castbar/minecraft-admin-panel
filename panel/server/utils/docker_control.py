"""
Módulo para controlar contenedores Docker desde Django
"""
import json
import os
from typing import Optional, Dict, List
import docker

def _get_docker_client():
    """Obtener cliente Docker conectado al socket"""
    try:
        return docker.from_env()
    except Exception as e:
        raise Exception(f'Error conectando a Docker: {str(e)}')

def docker_command(command: List[str], timeout: int = 30) -> Dict[str, any]:
    """
    Ejecutar comando Docker usando la librería de Python (compatibilidad)
    
    NOTA: Esta función se mantiene para compatibilidad, pero ahora usa la librería docker
    en lugar de subprocess, ya que el contenedor no tiene el CLI de Docker instalado.
    
    Args:
        command: Lista de argumentos para docker (ej: ['ps', '-a'])
        timeout: Timeout en segundos (no usado con la librería)
    
    Returns:
        Dict con 'success', 'output', 'error'
    """
    try:
        client = _get_docker_client()
        
        # Mapear comandos comunes a métodos de la librería
        cmd = command[0] if command else None
        
        if cmd == 'inspect':
            container_name = command[1] if len(command) > 1 else None
            if not container_name:
                return {'success': False, 'error': 'Container name required for inspect'}
            
            try:
                container = client.containers.get(container_name)
                if '--format' in command:
                    # Si hay formato JSON, devolver JSON
                    format_idx = command.index('--format')
                    if format_idx + 1 < len(command):
                        format_str = command[format_idx + 1]
                        if 'json' in format_str.lower():
                            import json
                            return {
                                'success': True,
                                'output': json.dumps(container.attrs),
                                'error': None,
                                'returncode': 0
                            }
                        # Si es formato simple, extraer el campo
                        if '{{.State.Status}}' in format_str:
                            return {
                                'success': True,
                                'output': container.status,
                                'error': None,
                                'returncode': 0
                            }
                
                # Por defecto, devolver JSON completo
                return {
                    'success': True,
                    'output': json.dumps(container.attrs),
                    'error': None,
                    'returncode': 0
                }
            except docker.errors.NotFound:
                return {
                    'success': False,
                    'error': f'No such container: {container_name}',
                    'output': '',
                    'returncode': 1
                }
        
        # Para otros comandos, usar métodos directos de la librería
        return {
            'success': False,
            'error': f'Comando no soportado directamente: {cmd}. Use las funciones específicas.',
            'output': '',
            'returncode': -1
        }
    except Exception as e:
        return {
            'success': False,
            'output': '',
            'error': str(e),
            'returncode': -1
        }

def get_container_status(container_name: str) -> Optional[str]:
    """
    Obtener estado de un contenedor Docker
    
    Returns:
        'running', 'paused', 'stopped', 'not_found', None si error
    """
    try:
        client = _get_docker_client()
        container = client.containers.get(container_name)
        status = container.status.lower()
        
        if status == 'running':
            return 'running'
        elif status == 'paused':
            return 'paused'
        elif status in ['exited', 'stopped', 'dead', 'created']:
            return 'stopped'
        else:
            return status
    except docker.errors.NotFound:
        return 'not_found'
    except Exception as e:
        print(f"Error obteniendo estado del contenedor: {e}")
        return None

def start_container(container_name: str) -> Dict[str, any]:
    """
    Iniciar un contenedor Docker
    
    Returns:
        Dict con 'success', 'message', 'error'
    """
    try:
        client = _get_docker_client()
        container = client.containers.get(container_name)
        
        # Verificar estado actual
        status = container.status.lower()
        
        if status == 'running':
            return {
                'success': True,
                'message': f'Contenedor {container_name} ya está en ejecución',
                'status': 'running'
            }
        
        # Restaurar política de reinicio antes de iniciar
        container.update(restart_policy={"Name": "unless-stopped"})
        
        # Iniciar contenedor
        container.start()
        
        return {
            'success': True,
            'message': f'Contenedor {container_name} iniciado correctamente',
            'status': 'running'
        }
    except docker.errors.NotFound:
        return {
            'success': False,
            'error': f'Contenedor {container_name} no existe',
            'status': 'not_found'
        }
    except Exception as e:
        status = get_container_status(container_name)
        return {
            'success': False,
            'error': str(e) or 'Error desconocido al iniciar contenedor',
            'status': status
        }

def stop_container(container_name: str, timeout: int = 10) -> Dict[str, any]:
    """
    Detener un contenedor Docker
    
    Args:
        container_name: Nombre del contenedor
        timeout: Tiempo de espera antes de forzar detención
    
    Returns:
        Dict con 'success', 'message', 'error'
    """
    try:
        client = _get_docker_client()
        container = client.containers.get(container_name)
        
        # Verificar estado actual
        status = container.status.lower()
        
        if status in ['exited', 'stopped', 'dead', 'created']:
            return {
                'success': True,
                'message': f'Contenedor {container_name} ya está detenido',
                'status': 'stopped'
            }
        
        # Primero, desactivar la política de reinicio para evitar que Docker reinicie el contenedor
        container.update(restart_policy={"Name": "no"})
        
        # Detener contenedor
        container.stop(timeout=timeout)
        
        return {
            'success': True,
            'message': f'Contenedor {container_name} detenido correctamente',
            'status': 'stopped'
        }
    except docker.errors.NotFound:
        return {
            'success': False,
            'error': f'Contenedor {container_name} no existe',
            'status': 'not_found'
        }
    except Exception as e:
        status = get_container_status(container_name)
        return {
            'success': False,
            'error': str(e) or 'Error desconocido al detener contenedor',
            'status': status
        }

def restart_container(container_name: str, timeout: int = 10) -> Dict[str, any]:
    """
    Reiniciar un contenedor Docker
    
    Returns:
        Dict con 'success', 'message', 'error'
    """
    try:
        client = _get_docker_client()
        container = client.containers.get(container_name)
        
        # Reiniciar contenedor
        container.restart(timeout=timeout)
        
        return {
            'success': True,
            'message': f'Contenedor {container_name} reiniciado correctamente',
            'status': 'running'
        }
    except docker.errors.NotFound:
        return {
            'success': False,
            'error': f'Contenedor {container_name} no existe',
            'status': 'not_found'
        }
    except Exception as e:
        status = get_container_status(container_name)
        return {
            'success': False,
            'error': str(e) or 'Error desconocido al reiniciar contenedor',
            'status': status
        }

def pause_container(container_name: str) -> Dict[str, any]:
    """
    Pausar un contenedor Docker (suspende procesos)
    
    Returns:
        Dict con 'success', 'message', 'error'
    """
    try:
        client = _get_docker_client()
        container = client.containers.get(container_name)
        
        status = container.status.lower()
        
        if status != 'running':
            return {
                'success': False,
                'error': f'Contenedor {container_name} no está en ejecución (estado: {status})',
                'status': status
            }
        
        container.pause()
        
        return {
            'success': True,
            'message': f'Contenedor {container_name} pausado correctamente',
            'status': 'paused'
        }
    except docker.errors.NotFound:
        return {
            'success': False,
            'error': f'Contenedor {container_name} no existe',
            'status': 'not_found'
        }
    except Exception as e:
        status = get_container_status(container_name)
        return {
            'success': False,
            'error': str(e) or 'Error desconocido al pausar contenedor',
            'status': status
        }

def unpause_container(container_name: str) -> Dict[str, any]:
    """
    Reanudar un contenedor Docker pausado
    
    Returns:
        Dict con 'success', 'message', 'error'
    """
    try:
        client = _get_docker_client()
        container = client.containers.get(container_name)
        
        status = container.status.lower()
        
        if status != 'paused':
            return {
                'success': False,
                'error': f'Contenedor {container_name} no está pausado (estado: {status})',
                'status': status
            }
        
        container.unpause()
        
        return {
            'success': True,
            'message': f'Contenedor {container_name} reanudado correctamente',
            'status': 'running'
        }
    except docker.errors.NotFound:
        return {
            'success': False,
            'error': f'Contenedor {container_name} no existe',
            'status': 'not_found'
        }
    except Exception as e:
        status = get_container_status(container_name)
        return {
            'success': False,
            'error': str(e) or 'Error desconocido al reanudar contenedor',
            'status': status
        }

def create_container_from_compose(service_name: str, compose_file: str = None) -> Dict[str, any]:
    """
    Crear e iniciar un contenedor usando docker-compose
    
    Args:
        service_name: Nombre del servicio en docker-compose
        compose_file: Ruta al archivo docker-compose.yml (opcional)
    
    Returns:
        Dict con 'success', 'message', 'error'
    """
    command = ['compose', 'up', '-d', service_name]
    
    if compose_file:
        command.extend(['-f', compose_file])
    
    result = docker_command(command, timeout=60)
    
    if result['success']:
        return {
            'success': True,
            'message': f'Servicio {service_name} creado e iniciado correctamente',
            'output': result['output']
        }
    else:
        return {
            'success': False,
            'error': result['error'] or 'Error desconocido al crear contenedor',
            'output': result['output']
        }

def create_minecraft_container(server) -> Dict[str, any]:
    """
    Crear un contenedor Docker para un servidor Minecraft usando docker SDK
    
    Args:
        server: Instancia del modelo Server
    
    Returns:
        Dict con 'success', 'message', 'error', 'status'
    """
    try:
        client = _get_docker_client()
        
        # Verificar si el contenedor ya existe
        try:
            existing = client.containers.get(server.container_name)
            return {
                'success': False,
                'error': f'El contenedor {server.container_name} ya existe',
                'status': existing.status
            }
        except docker.errors.NotFound:
            pass  # El contenedor no existe, continuar con la creación
        
        # Determinar imagen según tipo de servidor
        image_map = {
            'vanilla': 'itzg/minecraft-server:latest',
            'paper': 'itzg/minecraft-server:latest',
            'spigot': 'itzg/minecraft-server:latest',
            'bukkit': 'itzg/minecraft-server:latest',
            'fabric': 'itzg/minecraft-server:latest',
            'forge': 'itzg/minecraft-server:latest',
        }
        image = image_map.get(server.server_type, 'itzg/minecraft-server:latest')
        
        # Preparar variables de entorno
        env_vars = {
            'EULA': 'TRUE',
            'TYPE': server.server_type.upper(),
            'VERSION': server.minecraft_version if server.minecraft_version != 'latest' else 'LATEST',
            'MEMORY': f'{server.memory_limit_mb}M',
            'ENABLE_RCON': 'true',
            'RCON_PASSWORD': server.rcon_password,
            'RCON_PORT': str(server.rcon_port),
            'MAX_PLAYERS': str(server.max_players if hasattr(server, 'max_players') else 20),
            'ONLINE_MODE': 'true' if server.online_mode else 'false',
            'WHITELIST': 'true' if server.enable_whitelist else 'false',
        }
        
        # Agregar configuración adicional si existe
        if hasattr(server, 'motd') and server.motd:
            env_vars['MOTD'] = server.motd
        if hasattr(server, 'difficulty') and server.difficulty:
            env_vars['DIFFICULTY'] = server.difficulty
        
        # Crear volumen para los datos
        volume_name = f'{server.container_name}_data'
        
        # Crear volumen si no existe
        try:
            client.volumes.get(volume_name)
        except docker.errors.NotFound:
            client.volumes.create(name=volume_name, driver='local')
        
        # Preparar puertos
        ports = {}
        port_bindings = {}
        if hasattr(server, 'server_port') and server.server_port:
            ports['25565/tcp'] = {}
            port_bindings['25565/tcp'] = [{'HostPort': str(server.server_port), 'HostIp': '0.0.0.0'}]
        
        # Crear el contenedor
        container = client.containers.create(
            image=image,
            name=server.container_name,
            environment=env_vars,
            volumes={volume_name: {'bind': '/data', 'mode': 'rw'}},
            ports=ports,
            host_config=client.api.create_host_config(
                restart_policy={'Name': 'unless-stopped'},
                mem_limit=f'{server.memory_limit_mb}m',
                mem_reservation=f'{server.java_heap_min_mb}m',
                binds=[f'{volume_name}:/data:rw'],
                port_bindings=port_bindings if port_bindings else None,
            ),
            tty=True,
            stdin_open=True,
        )
        
        return {
            'success': True,
            'message': f'Contenedor {server.container_name} creado correctamente',
            'status': 'created',
            'container_id': container.id
        }
        
    except docker.errors.ImageNotFound:
        return {
            'success': False,
            'error': f'Imagen {image} no encontrada. Asegúrate de que la imagen esté disponible.',
            'status': 'error'
        }
    except docker.errors.APIError as e:
        return {
            'success': False,
            'error': f'Error de Docker API: {str(e)}',
            'status': 'error'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error al crear contenedor: {str(e)}',
            'status': 'error'
        }

def get_container_info(container_name: str) -> Dict[str, any]:
    """
    Obtener información detallada de un contenedor
    
    Returns:
        Dict con información del contenedor
    """
    try:
        client = _get_docker_client()
        container = client.containers.get(container_name)
        
        attrs = container.attrs
        state = attrs.get('State', {})
        config = attrs.get('Config', {})
        
        return {
            'success': True,
            'name': attrs.get('Name', '').lstrip('/'),
            'status': state.get('Status', 'unknown'),
            'running': state.get('Running', False),
            'paused': state.get('Paused', False),
            'restarting': state.get('Restarting', False),
            'started_at': state.get('StartedAt', ''),
            'image': config.get('Image', ''),
        }
    except docker.errors.NotFound:
        return {
            'success': False,
            'error': 'Contenedor no encontrado'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error obteniendo información del contenedor: {str(e)}'
        }

def update_container_memory(container_name: str, memory_limit_mb: int) -> Dict[str, any]:
    """
    Actualizar límite de memoria de un contenedor existente
    
    Nota: Docker requiere reiniciar el contenedor para aplicar cambios de memoria
    
    Args:
        container_name: Nombre del contenedor
        memory_limit_mb: Nuevo límite de memoria en MB
    
    Returns:
        Dict con 'success', 'message', 'error'
    """
    try:
        client = _get_docker_client()
        container = client.containers.get(container_name)
        
        # Actualizar límite de memoria
        memory_bytes = memory_limit_mb * 1024 * 1024  # Convertir MB a bytes
        container.update(mem_limit=memory_bytes, memswap_limit=memory_bytes)
        
        return {
            'success': True,
            'message': f'Límite de memoria actualizado a {memory_limit_mb}MB. Reinicia el contenedor para aplicar cambios.',
            'requires_restart': True
        }
    except docker.errors.NotFound:
        return {
            'success': False,
            'error': f'Contenedor {container_name} no existe'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e) or 'Error al actualizar límite de memoria'
        }

def get_recommended_memory(server_type: str, players_online: int = 0) -> Dict[str, int]:
    """
    Calcular memoria recomendada según tipo de servidor y jugadores
    
    Args:
        server_type: Tipo de servidor (vanilla, paper, fabric, forge)
        players_online: Número de jugadores online (opcional)
    
    Returns:
        Dict con 'memory_limit_mb', 'java_heap_max_mb', 'java_heap_min_mb'
    """
    # Memoria base según tipo
    base_memory = {
        'vanilla': 1024,
        'paper': 1024,
        'spigot': 1024,
        'bukkit': 1024,
        'fabric': 2048,
        'forge': 3072,
    }.get(server_type, 2048)
    
    # ~200MB por jugador
    player_memory = players_online * 200
    
    # Memoria total recomendada
    memory_limit_mb = base_memory + player_memory
    
    # Asegurar mínimo según tipo
    min_memory = {
        'vanilla': 1024,
        'paper': 1024,
        'fabric': 2048,
        'forge': 3072,
    }.get(server_type, 2048)
    
    memory_limit_mb = max(memory_limit_mb, min_memory)
    
    # Heap Java (dejar ~200MB para sistema)
    java_heap_max_mb = memory_limit_mb - 200
    java_heap_min_mb = min(512, java_heap_max_mb // 3)  # Mínimo 512MB o 1/3 del máximo
    
    return {
        'memory_limit_mb': memory_limit_mb,
        'java_heap_max_mb': java_heap_max_mb,
        'java_heap_min_mb': java_heap_min_mb
    }

