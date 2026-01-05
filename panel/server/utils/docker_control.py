"""
Módulo para controlar contenedores Docker desde Django
"""
import subprocess
import json
import os
from typing import Optional, Dict, List

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
    Obtener estado de un contenedor Docker
    
    Returns:
        'running', 'paused', 'stopped', 'not_found', None si error
    """
    result = docker_command(['inspect', container_name, '--format', '{{.State.Status}}'])
    
    if not result['success']:
        if 'No such container' in result['error']:
            return 'not_found'
        return None
    
    status = result['output'].lower()
    if status == 'running':
        return 'running'
    elif status == 'paused':
        return 'paused'
    elif status in ['exited', 'stopped', 'dead']:
        return 'stopped'
    else:
        return status

def start_container(container_name: str) -> Dict[str, any]:
    """
    Iniciar un contenedor Docker
    
    Returns:
        Dict con 'success', 'message', 'error'
    """
    # Verificar estado actual
    status = get_container_status(container_name)
    
    if status == 'running':
        return {
            'success': True,
            'message': f'Contenedor {container_name} ya está en ejecución',
            'status': 'running'
        }
    
    if status == 'not_found':
        return {
            'success': False,
            'error': f'Contenedor {container_name} no existe',
            'status': 'not_found'
        }
    
    # Iniciar contenedor
    result = docker_command(['start', container_name])
    
    if result['success']:
        return {
            'success': True,
            'message': f'Contenedor {container_name} iniciado correctamente',
            'status': 'running'
        }
    else:
        return {
            'success': False,
            'error': result['error'] or 'Error desconocido al iniciar contenedor',
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
    # Verificar estado actual
    status = get_container_status(container_name)
    
    if status == 'stopped' or status == 'not_found':
        return {
            'success': True,
            'message': f'Contenedor {container_name} ya está detenido',
            'status': 'stopped'
        }
    
    # Detener contenedor
    result = docker_command(['stop', '--time', str(timeout), container_name])
    
    if result['success']:
        return {
            'success': True,
            'message': f'Contenedor {container_name} detenido correctamente',
            'status': 'stopped'
        }
    else:
        return {
            'success': False,
            'error': result['error'] or 'Error desconocido al detener contenedor',
            'status': status
        }

def restart_container(container_name: str, timeout: int = 10) -> Dict[str, any]:
    """
    Reiniciar un contenedor Docker
    
    Returns:
        Dict con 'success', 'message', 'error'
    """
    result = docker_command(['restart', '--time', str(timeout), container_name])
    
    if result['success']:
        return {
            'success': True,
            'message': f'Contenedor {container_name} reiniciado correctamente',
            'status': 'running'
        }
    else:
        status = get_container_status(container_name)
        return {
            'success': False,
            'error': result['error'] or 'Error desconocido al reiniciar contenedor',
            'status': status
        }

def pause_container(container_name: str) -> Dict[str, any]:
    """
    Pausar un contenedor Docker (suspende procesos)
    
    Returns:
        Dict con 'success', 'message', 'error'
    """
    status = get_container_status(container_name)
    
    if status != 'running':
        return {
            'success': False,
            'error': f'Contenedor {container_name} no está en ejecución (estado: {status})',
            'status': status
        }
    
    result = docker_command(['pause', container_name])
    
    if result['success']:
        return {
            'success': True,
            'message': f'Contenedor {container_name} pausado correctamente',
            'status': 'paused'
        }
    else:
        return {
            'success': False,
            'error': result['error'] or 'Error desconocido al pausar contenedor',
            'status': status
        }

def unpause_container(container_name: str) -> Dict[str, any]:
    """
    Reanudar un contenedor Docker pausado
    
    Returns:
        Dict con 'success', 'message', 'error'
    """
    status = get_container_status(container_name)
    
    if status != 'paused':
        return {
            'success': False,
            'error': f'Contenedor {container_name} no está pausado (estado: {status})',
            'status': status
        }
    
    result = docker_command(['unpause', container_name])
    
    if result['success']:
        return {
            'success': True,
            'message': f'Contenedor {container_name} reanudado correctamente',
            'status': 'running'
        }
    else:
        return {
            'success': False,
            'error': result['error'] or 'Error desconocido al reanudar contenedor',
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

def get_container_info(container_name: str) -> Dict[str, any]:
    """
    Obtener información detallada de un contenedor
    
    Returns:
        Dict con información del contenedor
    """
    result = docker_command(['inspect', container_name, '--format', '{{json .}}'])
    
    if not result['success']:
        return {
            'success': False,
            'error': result['error'] or 'Contenedor no encontrado'
        }
    
    try:
        info = json.loads(result['output'])
        return {
            'success': True,
            'name': info.get('Name', '').lstrip('/'),
            'status': info.get('State', {}).get('Status', 'unknown'),
            'running': info.get('State', {}).get('Running', False),
            'paused': info.get('State', {}).get('Paused', False),
            'restarting': info.get('State', {}).get('Restarting', False),
            'started_at': info.get('State', {}).get('StartedAt', ''),
            'image': info.get('Config', {}).get('Image', ''),
        }
    except json.JSONDecodeError:
        return {
            'success': False,
            'error': 'Error al parsear información del contenedor'
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
    # Verificar que el contenedor existe
    status = get_container_status(container_name)
    if status == 'not_found':
        return {
            'success': False,
            'error': f'Contenedor {container_name} no existe'
        }
    
    # Actualizar límite de memoria usando docker update
    result = docker_command([
        'update',
        '--memory', f'{memory_limit_mb}m',
        '--memory-swap', f'{memory_limit_mb}m',
        container_name
    ])
    
    if result['success']:
        return {
            'success': True,
            'message': f'Límite de memoria actualizado a {memory_limit_mb}MB. Reinicia el contenedor para aplicar cambios.',
            'requires_restart': True
        }
    else:
        return {
            'success': False,
            'error': result['error'] or 'Error al actualizar límite de memoria'
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

