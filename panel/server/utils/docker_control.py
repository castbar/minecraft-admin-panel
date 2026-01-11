"""
Módulo para controlar contenedores Docker desde Django
"""
import subprocess
import json
import os
from typing import Optional, Dict, List

# Intentar importar la librería docker de Python (disponible en contenedores)
try:
    import docker
    DOCKER_LIB_AVAILABLE = True
except ImportError:
    DOCKER_LIB_AVAILABLE = False
    docker = None

def _get_docker_client():
    """Obtener cliente Docker conectado al socket"""
    if not DOCKER_LIB_AVAILABLE:
        raise Exception('Librería docker de Python no está disponible. Use subprocess en su lugar.')
    try:
        return docker.from_env()
    except Exception as e:
        raise Exception(f'Error conectando a Docker: {str(e)}')

def docker_command(command: List[str], timeout: int = 30) -> Dict[str, any]:
    """
    Ejecutar comando Docker y retornar resultado
    
    Args:
        command: Lista de argumentos para docker (ej: ['ps', '-a'])
        timeout: Timeout en segundos
    
    Returns:
        Dict con 'success', 'output', 'error'
    """
    try:
        result = subprocess.run(
            ['docker'] + command,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        return {
            'success': result.returncode == 0,
            'output': result.stdout.strip(),
            'error': result.stderr.strip() if result.returncode != 0 else None,
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'output': '',
            'error': f'Timeout después de {timeout} segundos',
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
    Obtener estado de un contenedor Docker usando la librería docker de Python
    
    Returns:
        'running', 'paused', 'stopped', 'not_found', None si error
    """
    # Usar SOLO la librería docker de Python (no usar subprocess)
    if not DOCKER_LIB_AVAILABLE:
        # Si la librería no está disponible, devolver 'not_found' en lugar de intentar usar subprocess
        return 'not_found'
    
    try:
        client = _get_docker_client()
        container = client.containers.get(container_name)
        status = container.status.lower()
        if status == 'running':
            return 'running'
        elif status == 'paused':
            return 'paused'
        elif status in ['exited', 'stopped', 'dead']:
            return 'stopped'
        else:
            return status
    except docker.errors.NotFound:
        return 'not_found'
    except Exception as e:
        # Si hay un error, devolver 'not_found' en lugar de None para evitar falsos positivos
        print(f"Error obteniendo estado del contenedor {container_name}: {e}")
        return 'not_found'

def start_container(container_name: str) -> Dict[str, any]:
    """
    Iniciar un contenedor Docker usando la librería docker de Python
    
    Returns:
        Dict con 'success', 'message', 'error'
    """
    if not DOCKER_LIB_AVAILABLE:
        return {
            'success': False,
            'error': 'Librería docker de Python no está disponible',
            'status': None
        }
    
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
        return {
            'success': False,
            'error': f'Error al iniciar contenedor: {str(e)}',
            'status': None
        }

def stop_container(container_name: str, timeout: int = 10) -> Dict[str, any]:
    """
    Detener un contenedor Docker usando la librería docker de Python
    
    Args:
        container_name: Nombre del contenedor
        timeout: Tiempo de espera antes de forzar detención
    
    Returns:
        Dict con 'success', 'message', 'error'
    """
    if not DOCKER_LIB_AVAILABLE:
        return {
            'success': False,
            'error': 'Librería docker de Python no está disponible',
            'status': None
        }
    
    try:
        client = _get_docker_client()
        container = client.containers.get(container_name)
        
        # Verificar estado actual
        status = container.status.lower()
        
        if status in ['stopped', 'exited', 'dead']:
            return {
                'success': True,
                'message': f'Contenedor {container_name} ya está detenido',
                'status': 'stopped'
            }
        
        # Detener contenedor
        container.stop(timeout=timeout)
        
        return {
            'success': True,
            'message': f'Contenedor {container_name} detenido correctamente',
            'status': 'stopped'
        }
    except docker.errors.NotFound:
        return {
            'success': True,
            'message': f'Contenedor {container_name} no existe',
            'status': 'not_found'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error al detener contenedor: {str(e)}',
            'status': None
        }

def restart_container(container_name: str, timeout: int = 10) -> Dict[str, any]:
    """
    Reiniciar un contenedor Docker usando la librería docker de Python
    
    Returns:
        Dict con 'success', 'message', 'error'
    """
    if not DOCKER_LIB_AVAILABLE:
        return {
            'success': False,
            'error': 'Librería docker de Python no está disponible',
            'status': None
        }
    
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
        return {
            'success': False,
            'error': f'Error al reiniciar contenedor: {str(e)}',
            'status': None
        }

def pause_container(container_name: str) -> Dict[str, any]:
    """
    Pausar un contenedor Docker (suspende procesos) usando la librería docker de Python
    
    Returns:
        Dict con 'success', 'message', 'error'
    """
    if not DOCKER_LIB_AVAILABLE:
        return {
            'success': False,
            'error': 'Librería docker de Python no está disponible',
            'status': None
        }
    
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
        return {
            'success': False,
            'error': f'Error al pausar contenedor: {str(e)}',
            'status': None
        }

def unpause_container(container_name: str) -> Dict[str, any]:
    """
    Reanudar un contenedor Docker pausado usando la librería docker de Python
    
    Returns:
        Dict con 'success', 'message', 'error'
    """
    if not DOCKER_LIB_AVAILABLE:
        return {
            'success': False,
            'error': 'Librería docker de Python no está disponible',
            'status': None
        }
    
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
        return {
            'success': False,
            'error': f'Error al reanudar contenedor: {str(e)}',
            'status': None
        }

def create_container_from_compose(service_name: str, compose_file: str = None) -> Dict[str, any]:
    """
    Crear e iniciar un contenedor usando docker-compose
    
    NOTA: Esta función requiere el CLI de docker-compose, que puede no estar disponible.
    Para crear contenedores individuales, usa create_minecraft_container en su lugar.
    
    Args:
        service_name: Nombre del servicio en docker-compose
        compose_file: Ruta al archivo docker-compose.yml (opcional)
    
    Returns:
        Dict con 'success', 'message', 'error'
    """
    # docker-compose requiere el CLI, usar subprocess directamente
    try:
        command = ['docker', 'compose', 'up', '-d', service_name]
        
        if compose_file:
            command.extend(['-f', compose_file])
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return {
                'success': True,
                'message': f'Servicio {service_name} creado e iniciado correctamente',
                'output': result.stdout.strip()
            }
        else:
            return {
                'success': False,
                'error': result.stderr.strip() or 'Error desconocido al crear contenedor',
                'output': result.stdout.strip()
            }
    except FileNotFoundError:
        return {
            'success': False,
            'error': 'docker-compose no está disponible. Use create_minecraft_container para crear contenedores individuales.',
            'output': ''
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Timeout al ejecutar docker-compose',
            'output': ''
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error al ejecutar docker-compose: {str(e)}',
            'output': ''
        }

def get_container_info(container_name: str) -> Dict[str, any]:
    """
    Obtener información detallada de un contenedor usando la librería docker de Python
    
    Returns:
        Dict con información del contenedor
    """
    if not DOCKER_LIB_AVAILABLE:
        return {
            'success': False,
            'error': 'Librería docker de Python no está disponible'
        }
    
    try:
        client = _get_docker_client()
        container = client.containers.get(container_name)
        
        # Obtener información del contenedor
        attrs = container.attrs
        
        return {
            'success': True,
            'name': attrs.get('Name', '').lstrip('/'),
            'status': attrs.get('State', {}).get('Status', 'unknown'),
            'running': attrs.get('State', {}).get('Running', False),
            'paused': attrs.get('State', {}).get('Paused', False),
            'restarting': attrs.get('State', {}).get('Restarting', False),
            'started_at': attrs.get('State', {}).get('StartedAt', ''),
            'image': attrs.get('Config', {}).get('Image', ''),
        }
    except docker.errors.NotFound:
        return {
            'success': False,
            'error': 'Contenedor no encontrado'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error al obtener información del contenedor: {str(e)}'
        }

def update_container_memory(container_name: str, memory_limit_mb: int) -> Dict[str, any]:
    """
    Actualizar límite de memoria de un contenedor existente usando la librería docker de Python
    
    Nota: Docker requiere reiniciar el contenedor para aplicar cambios de memoria
    
    Args:
        container_name: Nombre del contenedor
        memory_limit_mb: Nuevo límite de memoria en MB
    
    Returns:
        Dict con 'success', 'message', 'error'
    """
    if not DOCKER_LIB_AVAILABLE:
        return {
            'success': False,
            'error': 'Librería docker de Python no está disponible'
        }
    
    try:
        client = _get_docker_client()
        container = client.containers.get(container_name)
        
        # Actualizar límite de memoria usando update()
        container.update(mem_limit=f'{memory_limit_mb}m', memswap_limit=f'{memory_limit_mb}m')
        
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
            'error': f'Error al actualizar límite de memoria: {str(e)}'
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

def create_minecraft_container(
    container_name: str,
    server_type: str,
    minecraft_version: str,
    rcon_port: int,
    rcon_password: str,
    memory_limit_mb: int,
    java_heap_max_mb: int,
    java_heap_min_mb: int,
    minecraft_data_path: str = '/data',
    minecraft_port: int = 25565,
    network: str = 'minecraft-servers',
    start_container: bool = True,
    additional_ports: List[Dict[str, any]] = None
) -> Dict[str, any]:
    """
    Crear un contenedor Docker para un servidor Minecraft
    
    Args:
        container_name: Nombre del contenedor
        server_type: Tipo de servidor (vanilla, paper, fabric, forge, spigot, bukkit)
        minecraft_version: Versión de Minecraft (ej: 'latest', '1.20.1')
        rcon_port: Puerto RCON
        rcon_password: Contraseña RCON
        memory_limit_mb: Límite de memoria en MB
        java_heap_max_mb: Heap máximo de Java en MB
        java_heap_min_mb: Heap mínimo de Java en MB
        minecraft_data_path: Ruta donde se montarán los datos (default: /data)
        minecraft_port: Puerto del servidor Minecraft (default: 25565)
        network: Red Docker a la que conectar (default: minecraft-servers)
        start_container: Si True, inicia el contenedor después de crearlo (default: True)
    
    Returns:
        Dict con 'success', 'message', 'error', 'container_id'
    """
    try:
        if not DOCKER_LIB_AVAILABLE:
            return {
                'success': False,
                'error': 'Librería docker de Python no está disponible. No se puede crear contenedores.'
            }
        
        import docker
        
        # Verificar si el contenedor ya existe usando la librería directamente
        try:
            client = _get_docker_client()
            existing_container = client.containers.get(container_name)
            # Si llegamos aquí, el contenedor existe
            return {
                'success': False,
                'error': f'El contenedor {container_name} ya existe (estado: {existing_container.status})'
            }
        except docker.errors.NotFound:
            # El contenedor no existe, continuar con la creación
            pass
        except Exception as e:
            # Si hay otro error al verificar, asumir que no existe y continuar
            # (mejor intentar crear y fallar si realmente existe, que bloquear incorrectamente)
            print(f"Error verificando existencia del contenedor {container_name}: {e}")
            pass
        
        # Obtener cliente Docker
        client = _get_docker_client()
        
        # Mapear tipos de servidor a imágenes Docker
        # Usamos itzg/minecraft-server que soporta múltiples tipos mediante variables de entorno
        image_map = {
            'vanilla': 'itzg/minecraft-server',
            'paper': 'itzg/minecraft-server',
            'spigot': 'itzg/minecraft-server',
            'bukkit': 'itzg/minecraft-server',
            'fabric': 'itzg/minecraft-server',
            'forge': 'itzg/minecraft-server',
        }
        
        docker_image = image_map.get(server_type, 'itzg/minecraft-server')
        
        # Asegurar que la imagen esté disponible (pull si es necesario)
        try:
            client.images.get(docker_image)
        except docker.errors.ImageNotFound:
            # Intentar hacer pull de la imagen
            try:
                print(f"Descargando imagen {docker_image}...")
                client.images.pull(docker_image)
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Error al descargar imagen {docker_image}: {str(e)}'
                }
        
        # Variables de entorno
        env_vars = {
            'EULA': 'TRUE',
            'TYPE': server_type.upper(),
            'VERSION': minecraft_version,
            'ENABLE_RCON': 'true',
            'RCON_PORT': '25575',
            'RCON_PASSWORD': rcon_password,
            'MAX_MEMORY': f'{java_heap_max_mb}M',
            'INIT_MEMORY': f'{java_heap_min_mb}M',
            'ONLINE_MODE': 'FALSE',  # Permitir clientes no premium por defecto
        }
        
        # Configurar tipo específico
        if server_type == 'paper':
            env_vars['PAPER_VERSION'] = 'latest'
        elif server_type == 'spigot':
            env_vars['SPIGOT_VERSION'] = 'latest'
        elif server_type == 'bukkit':
            env_vars['BUKKIT_VERSION'] = 'latest'
        elif server_type == 'fabric':
            env_vars['FABRIC_VERSION'] = 'latest'
        elif server_type == 'forge':
            env_vars['FORGE_VERSION'] = 'latest'
        
        # Configurar puertos
        ports = {
            '25565/tcp': minecraft_port,
            '25575/tcp': rcon_port
        }
        
        # Agregar puertos adicionales si se proporcionan
        if additional_ports:
            for port_config in additional_ports:
                container_port = port_config.get('port', port_config.get('container_port'))
                host_port = port_config.get('host_port', container_port)
                protocol = port_config.get('protocol', 'tcp').lower()
                
                if container_port and protocol in ['tcp', 'udp']:
                    port_key = f'{container_port}/{protocol}'
                    ports[port_key] = host_port
        
        # Configurar volúmenes
        volume_name = f'{container_name}_data'
        volumes = {
            volume_name: {
                'bind': minecraft_data_path,
                'mode': 'rw'
            }
        }
        
        # Verificar que la red existe, si no, crearla
        try:
            docker_network = client.networks.get(network)
        except docker.errors.NotFound:
            # Crear la red si no existe
            try:
                docker_network = client.networks.create(network, driver='bridge')
                print(f"Red {network} creada")
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Error al crear red {network}: {str(e)}'
                }
        
        # Obtener información del proyecto docker-compose desde el contenedor del panel
        # Esto permite que los servidores pertenezcan al mismo stack
        compose_labels = {}
        try:
            # Intentar obtener las labels del contenedor del panel
            panel_container = client.containers.get('minecraft-admin-panel')
            panel_labels = panel_container.labels
            
            # Extraer las labels de docker-compose del panel
            compose_project = panel_labels.get('com.docker.compose.project', 'minecraft-admin-panel')
            compose_config = panel_labels.get('com.docker.compose.project.config_files', 'docker-compose.yml')
            compose_working_dir = panel_labels.get('com.docker.compose.project.working_dir', '/app')
            
            # Agregar labels de docker-compose para que pertenezca al mismo proyecto
            compose_labels = {
                'com.docker.compose.project': compose_project,
                'com.docker.compose.project.config_files': compose_config,
                'com.docker.compose.project.working_dir': compose_working_dir,
                'com.docker.compose.service': f'minecraft-server-{container_name}',
                'com.docker.compose.container-number': '1',
                'com.docker.compose.oneoff': 'False',
            }
        except Exception as e:
            # Si no se puede obtener la info del panel, usar valores por defecto
            print(f"Advertencia: No se pudieron obtener labels del panel: {e}")
            compose_labels = {
                'com.docker.compose.project': 'minecraft-admin-panel',
                'com.docker.compose.service': f'minecraft-server-{container_name}',
                'com.docker.compose.oneoff': 'False',
            }
        
        # Crear el contenedor usando la librería docker con labels de compose
        container = client.containers.create(
            image=docker_image,
            name=container_name,
            environment=env_vars,
            ports=ports,
            volumes=volumes,
            network=network,
            mem_limit=f'{memory_limit_mb}m',
            memswap_limit=f'{memory_limit_mb}m',
            restart_policy={'Name': 'unless-stopped'},
            labels=compose_labels,
            detach=True
        )
        
        container_id = container.id
        
        # Si se solicita iniciar el contenedor
        if start_container:
            container.start()
        
        return {
            'success': True,
            'message': f'Contenedor {container_name} creado correctamente',
            'container_id': container_id
        }
        
    except docker.errors.APIError as e:
        return {
            'success': False,
            'error': f'Error de API de Docker: {str(e)}',
            'output': ''
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error al crear contenedor: {str(e)}',
            'output': ''
        }

def delete_container(container_name: str, force: bool = False, remove_volumes: bool = False) -> Dict[str, any]:
    """
    Eliminar un contenedor Docker usando la librería docker de Python
    
    Args:
        container_name: Nombre del contenedor
        force: Si True, fuerza la eliminación incluso si está corriendo
        remove_volumes: Si True, elimina también los volúmenes asociados
    
    Returns:
        Dict con 'success', 'message', 'error'
    """
    if not DOCKER_LIB_AVAILABLE:
        return {
            'success': False,
            'error': 'Librería docker de Python no está disponible',
            'status': None
        }
    
    try:
        client = _get_docker_client()
        
        # Verificar si el contenedor existe
        try:
            container = client.containers.get(container_name)
        except docker.errors.NotFound:
            return {
                'success': True,
                'message': f'El contenedor {container_name} no existe',
                'status': 'not_found'
            }
        
        # Si está corriendo, detenerlo primero (siempre, incluso con force)
        status = container.status.lower()
        if status == 'running':
            print(f"🛑 Deteniendo contenedor {container_name}...")
            stop_result = stop_container(container_name)
            if not stop_result['success']:
                print(f"⚠️ No se pudo detener el contenedor: {stop_result.get('error')}")
                # Continuar de todas formas si force=True
                if not force:
                    return {
                        'success': False,
                        'error': f'No se pudo detener el contenedor: {stop_result.get("error")}'
                    }
            # Esperar un momento para que Docker procese el stop
            import time
            time.sleep(1)
            # Refrescar el objeto container después de detenerlo
            try:
                container.reload()
            except:
                pass
        
        # Eliminar el contenedor
        print(f"🗑️ Eliminando contenedor {container_name}...")
        container.remove(force=force, v=remove_volumes)
        
        # Esperar un momento para que Docker libere los puertos
        import time
        time.sleep(1)
        
        return {
            'success': True,
            'message': f'Contenedor {container_name} eliminado correctamente'
        }
    except docker.errors.NotFound:
        return {
            'success': True,
            'message': f'El contenedor {container_name} no existe',
            'status': 'not_found'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error al eliminar contenedor: {str(e)}',
            'output': ''
        }

def find_containers_using_port(port: int) -> List[Dict[str, any]]:
    """
    Encontrar todos los contenedores que están usando un puerto específico
    
    Args:
        port: Puerto a buscar
    
    Returns:
        Lista de dicts con información de contenedores que usan el puerto
    """
    if not DOCKER_LIB_AVAILABLE:
        return []
    
    try:
        client = _get_docker_client()
        containers = client.containers.list(all=True)
        result = []
        
        for container in containers:
            try:
                # Verificar en HostConfig.PortBindings
                port_bindings = container.attrs.get('HostConfig', {}).get('PortBindings', {})
                if port_bindings:
                    for container_port, bindings in port_bindings.items():
                        if bindings:
                            for binding in bindings if isinstance(bindings, list) else [bindings]:
                                if binding.get('HostPort') == str(port):
                                    result.append({
                                        'name': container.name,
                                        'id': container.id[:12],
                                        'status': container.status,
                                        'port': port,
                                        'container_port': container_port
                                    })
                
                # También verificar en NetworkSettings.Ports
                network_ports = container.attrs.get('NetworkSettings', {}).get('Ports', {})
                for container_port, port_bindings in network_ports.items():
                    if port_bindings:
                        for binding in port_bindings if isinstance(port_bindings, list) else [port_bindings]:
                            if binding.get('HostPort') == str(port):
                                # Evitar duplicados
                                if not any(c['name'] == container.name for c in result):
                                    result.append({
                                        'name': container.name,
                                        'id': container.id[:12],
                                        'status': container.status,
                                        'port': port,
                                        'container_port': container_port
                                    })
            except Exception as e:
                print(f"Error verificando puertos del contenedor {container.name}: {e}")
                continue
        
        return result
    except Exception as e:
        print(f"Error buscando contenedores usando puerto {port}: {e}")
        return []

def cleanup_containers_blocking_ports(ports: List[int], exclude_container_name: str = None) -> Dict[str, any]:
    """
    Limpiar contenedores detenidos que están bloqueando puertos específicos
    
    Args:
        ports: Lista de puertos a verificar
        exclude_container_name: Nombre del contenedor a excluir de la limpieza
    
    Returns:
        Dict con información de contenedores eliminados
    """
    if not DOCKER_LIB_AVAILABLE:
        return {
            'success': False,
            'error': 'Librería docker de Python no está disponible',
            'removed': []
        }
    
    removed_containers = []
    errors = []
    
    try:
        for port in ports:
            containers_using_port = find_containers_using_port(port)
            
            for container_info in containers_using_port:
                container_name = container_info['name']
                container_status = container_info['status'].lower()
                
                # Excluir el contenedor especificado
                if exclude_container_name and container_name == exclude_container_name:
                    continue
                
                # Solo eliminar contenedores detenidos
                if container_status in ['exited', 'stopped', 'dead', 'created']:
                    try:
                        print(f"🗑️ Eliminando contenedor detenido {container_name} que bloquea puerto {port}...")
                        delete_result = delete_container(container_name, force=True)
                        if delete_result.get('success'):
                            removed_containers.append({
                                'name': container_name,
                                'port': port,
                                'status': container_status
                            })
                            # Esperar un momento para que Docker libere el puerto
                            import time
                            time.sleep(1)
                        else:
                            errors.append(f"No se pudo eliminar {container_name}: {delete_result.get('error')}")
                    except Exception as e:
                        errors.append(f"Error al eliminar {container_name}: {str(e)}")
                else:
                    errors.append(f"Contenedor {container_name} está {container_status} y bloquea puerto {port}. Deténlo manualmente primero.")
        
        return {
            'success': len(errors) == 0,
            'removed': removed_containers,
            'errors': errors,
            'message': f'Eliminados {len(removed_containers)} contenedor(es) que bloqueaban puertos'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error al limpiar contenedores: {str(e)}',
            'removed': removed_containers,
            'errors': errors
        }

def find_available_port(start_port: int = 25565, end_port: int = 26000, exclude_ports: List[int] = None) -> Optional[int]:
    """
    Encontrar un puerto disponible en el rango especificado
    
    Args:
        start_port: Puerto inicial del rango
        end_port: Puerto final del rango
        exclude_ports: Lista de puertos a excluir de la búsqueda
    
    Returns:
        Puerto disponible o None si no se encuentra ninguno
    """
    if not DOCKER_LIB_AVAILABLE:
        return None
    
    if exclude_ports is None:
        exclude_ports = []
    
    try:
        client = _get_docker_client()
        containers = client.containers.list(all=True)
        
        # Obtener todos los puertos en uso
        used_ports = set(exclude_ports)
        
        for container in containers:
            try:
                # Verificar en HostConfig.PortBindings
                port_bindings = container.attrs.get('HostConfig', {}).get('PortBindings', {})
                if port_bindings:
                    for container_port, bindings in port_bindings.items():
                        if bindings:
                            for binding in bindings if isinstance(bindings, list) else [bindings]:
                                host_port = binding.get('HostPort')
                                if host_port:
                                    try:
                                        used_ports.add(int(host_port))
                                    except ValueError:
                                        pass
                
                # También verificar en NetworkSettings.Ports
                network_ports = container.attrs.get('NetworkSettings', {}).get('Ports', {})
                for container_port, port_bindings in network_ports.items():
                    if port_bindings:
                        for binding in port_bindings if isinstance(port_bindings, list) else [port_bindings]:
                            host_port = binding.get('HostPort')
                            if host_port:
                                try:
                                    used_ports.add(int(host_port))
                                except ValueError:
                                    pass
            except Exception:
                continue
        
        # Buscar el primer puerto disponible
        for port in range(start_port, end_port + 1):
            if port not in used_ports:
                return port
        
        return None
    except Exception as e:
        print(f"Error buscando puerto disponible: {e}")
        return None

def find_available_ports_pair(minecraft_start: int = 25565, rcon_start: int = 25575, 
                               max_attempts: int = 100) -> Dict[str, Optional[int]]:
    """
    Encontrar un par de puertos disponibles (Minecraft y RCON) que estén cerca
    
    Args:
        minecraft_start: Puerto inicial para buscar puerto de Minecraft
        rcon_start: Puerto inicial para buscar puerto RCON
        max_attempts: Número máximo de intentos
    
    Returns:
        Dict con 'minecraft_port' y 'rcon_port' o None si no se encuentran
    """
    minecraft_port = None
    rcon_port = None
    
    # Intentar encontrar puertos cercanos
    for attempt in range(max_attempts):
        # Buscar puerto de Minecraft
        if not minecraft_port:
            minecraft_port = find_available_port(
                start_port=minecraft_start + attempt,
                end_port=minecraft_start + attempt + 50,
                exclude_ports=[rcon_start + attempt] if rcon_port is None else []
            )
        
        # Buscar puerto RCON (normalmente 10 puertos después del de Minecraft)
        if minecraft_port and not rcon_port:
            rcon_port = find_available_port(
                start_port=minecraft_start + attempt + 10,
                end_port=minecraft_start + attempt + 20,
                exclude_ports=[minecraft_port]
            )
        
        # Si encontramos ambos, retornar
        if minecraft_port and rcon_port:
            return {
                'minecraft_port': minecraft_port,
                'rcon_port': rcon_port
            }
        
        # Si no encontramos, resetear y buscar desde el siguiente bloque
        minecraft_port = None
        rcon_port = None
    
    # Si no encontramos puertos cercanos, buscar independientemente
    minecraft_port = find_available_port(start_port=minecraft_start, end_port=26000)
    rcon_port = find_available_port(start_port=rcon_start, end_port=26000, exclude_ports=[minecraft_port] if minecraft_port else [])
    
    return {
        'minecraft_port': minecraft_port,
        'rcon_port': rcon_port
    }
