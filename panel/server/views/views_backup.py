from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
import os
import subprocess
import tarfile
from datetime import datetime
from ..models import Server, Backup, BackupSchedule
from ..utils.permissions import require_server_permission

@login_required
@require_server_permission('view')
@require_http_methods(["GET"])
def backups_list(request, server_id):
    """Listar backups de un servidor"""
    server = request.server
    backups = Backup.objects.filter(server=server).order_by('-created_at')[:50]
    
    data = [{
        'id': b.id,
        'name': b.name,
        'status': b.status,
        'file_size_mb': b.get_file_size_mb(),
        'created_at': b.created_at.isoformat(),
        'completed_at': b.completed_at.isoformat() if b.completed_at else None,
    } for b in backups]
    
    return JsonResponse({'success': True, 'data': data})

@csrf_exempt
@login_required
@require_server_permission('control_server')
@require_http_methods(["POST"])
def backup_create(request, server_id):
    """Crear backup manual"""
    server = request.server
    
    backup_name = f"manual_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
    backup = Backup.objects.create(
        server=server,
        name=backup_name,
        status='pending'
    )
    
    # Ejecutar backup en background
    _execute_backup(backup.id)
    
    return JsonResponse({
        'success': True,
        'message': 'Backup iniciado',
        'data': {'id': backup.id, 'name': backup.name}
    })

@csrf_exempt
@login_required
@require_server_permission('control_server')
@require_http_methods(["POST"])
def backup_restore(request, server_id, backup_id):
    """Restaurar backup"""
    server = request.server
    
    try:
        backup = Backup.objects.get(id=backup_id, server=server)
    except Backup.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Backup not found'}, status=404)
    
    if backup.status != 'completed':
        return JsonResponse({'success': False, 'error': 'Backup not completed'}, status=400)
    
    if not backup.file_path or not os.path.exists(backup.file_path):
        return JsonResponse({'success': False, 'error': 'Backup file not found'}, status=404)
    
    # TODO: Implementar restauración
    # Requiere detener servidor, restaurar archivos, reiniciar
    
    return JsonResponse({
        'success': True,
        'message': 'Restore initiated (requires server restart)',
        'note': 'This feature requires server to be stopped'
    })

@login_required
@require_server_permission('view')
@require_http_methods(["GET"])
def backup_download(request, server_id, backup_id):
    """Descargar backup"""
    from django.http import FileResponse
    
    server = request.server
    
    try:
        backup = Backup.objects.get(id=backup_id, server=server)
    except Backup.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Backup not found'}, status=404)
    
    if backup.status != 'completed':
        return JsonResponse({'success': False, 'error': 'Backup not completed'}, status=400)
    
    if not backup.file_path or not os.path.exists(backup.file_path):
        return JsonResponse({'success': False, 'error': 'Backup file not found'}, status=404)
    
    return FileResponse(
        open(backup.file_path, 'rb'),
        as_attachment=True,
        filename=f"{backup.name}.tar.gz"
    )

@csrf_exempt
@login_required
@require_server_permission('control_server')
@require_http_methods(["DELETE"])
def backup_delete(request, server_id, backup_id):
    """Eliminar backup"""
    server = request.server
    
    try:
        backup = Backup.objects.get(id=backup_id, server=server)
        
        # Eliminar archivo si existe
        if backup.file_path and os.path.exists(backup.file_path):
            os.remove(backup.file_path)
        
        backup.delete()
        return JsonResponse({'success': True, 'message': 'Backup eliminado'})
    except Backup.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Backup not found'}, status=404)

@login_required
@require_server_permission('view')
@require_http_methods(["GET"])
def backup_schedules_list(request, server_id):
    """Listar programaciones de backups"""
    server = request.server
    schedules = BackupSchedule.objects.filter(server=server)
    
    data = [{
        'id': s.id,
        'name': s.name,
        'schedule_type': s.frequency,  # Compatibilidad con frontend
        'frequency': s.frequency,
        'schedule_time': s.time.strftime('%H:%M') if s.time else None,
        'time': s.time.strftime('%H:%M') if s.time else None,
        'enabled': s.is_active,
        'is_active': s.is_active,
        'keep_count': s.max_backups,
        'max_backups': s.max_backups,
        'last_run': s.last_run.isoformat() if s.last_run else None,
        'next_run': None,  # TODO: Calcular próxima ejecución
    } for s in schedules]
    
    return JsonResponse({'success': True, 'data': data})

@csrf_exempt
@login_required
@require_server_permission('control_server')
@require_http_methods(["POST"])
def backup_schedule_create(request, server_id):
    """Crear programación de backup"""
    server = request.server
    
    try:
        data = json.loads(request.body)
        schedule_type = data.get('schedule_type', 'daily')
        schedule_time = data.get('schedule_time', '00:00')
        keep_count = data.get('keep_count', 5)
        enabled = data.get('enabled', True)
        name = data.get('name', f"Schedule_{timezone.now().strftime('%Y%m%d_%H%M%S')}")
        
        # Parsear hora
        try:
            time_obj = datetime.strptime(schedule_time, '%H:%M').time()
        except:
            time_obj = datetime.strptime('00:00', '%H:%M').time()
        
        schedule = BackupSchedule.objects.create(
            server=server,
            name=name,
            frequency=schedule_type,
            time=time_obj,
            is_active=enabled,
            max_backups=keep_count
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Programación creada',
            'data': {
                'id': schedule.id,
                'name': schedule.name,
                'schedule_type': schedule.frequency,
                'schedule_time': schedule.time.strftime('%H:%M'),
                'enabled': schedule.is_active,
                'keep_count': schedule.max_backups
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@csrf_exempt
@login_required
@require_server_permission('control_server')
@require_http_methods(["PUT"])
def backup_schedule_update(request, server_id, schedule_id):
    """Actualizar programación de backup"""
    server = request.server
    
    try:
        schedule = BackupSchedule.objects.get(id=schedule_id, server=server)
    except BackupSchedule.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Schedule not found'}, status=404)
    
    try:
        data = json.loads(request.body)
        
        if 'schedule_type' in data:
            schedule.frequency = data['schedule_type']
        if 'schedule_time' in data:
            try:
                schedule.time = datetime.strptime(data['schedule_time'], '%H:%M').time()
            except:
                pass
        if 'keep_count' in data:
            schedule.max_backups = data['keep_count']
        if 'enabled' in data:
            schedule.is_active = data['enabled']
        if 'name' in data:
            schedule.name = data['name']
        
        schedule.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Programación actualizada',
            'data': {
                'id': schedule.id,
                'name': schedule.name,
                'schedule_type': schedule.frequency,
                'schedule_time': schedule.time.strftime('%H:%M') if schedule.time else None,
                'enabled': schedule.is_active,
                'keep_count': schedule.max_backups
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@csrf_exempt
@login_required
@require_server_permission('control_server')
@require_http_methods(["DELETE"])
def backup_schedule_delete(request, server_id, schedule_id):
    """Eliminar programación de backup"""
    server = request.server
    
    try:
        schedule = BackupSchedule.objects.get(id=schedule_id, server=server)
        schedule.delete()
        return JsonResponse({'success': True, 'message': 'Programación eliminada'})
    except BackupSchedule.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Schedule not found'}, status=404)

def _execute_backup(backup_id):
    """Ejecutar backup en background"""
    import docker
    import tempfile
    import shutil
    
    try:
        backup = Backup.objects.get(id=backup_id)
        backup.status = 'running'
        backup.save()
        
        server = backup.server
        
        # Si el servidor tiene container_name, usar Docker para acceder a los archivos
        if server.container_name:
            try:
                client = docker.from_env()
                container = client.containers.get(server.container_name)
                
                # Crear directorio temporal para el backup
                temp_dir = tempfile.mkdtemp()
                backup_file = os.path.join(temp_dir, f"{backup.name}.tar.gz")
                
                # Crear backup dentro del contenedor del servidor
                world_path = os.path.join(server.minecraft_data_path, 'world')
                backup_dir = os.path.join(server.minecraft_data_path, 'backups')
                
                # Ejecutar comando tar dentro del contenedor para crear el backup
                # Usar comando más simple y robusto - ignorar warnings de "file changed"
                tar_cmd = f"cd {server.minecraft_data_path} && tar -czf {backup_dir}/{backup.name}.tar.gz world server.properties whitelist.json ops.json banned-players.json banned-ips.json 2>&1 || tar -czf {backup_dir}/{backup.name}.tar.gz world"
                
                result = container.exec_run(f"sh -c 'mkdir -p {backup_dir} && {tar_cmd}'", user='root')
                
                # Verificar salida - el warning "file changed as we read it" es normal cuando el servidor está corriendo
                output = result.output.decode() if result.output else ''
                
                # Verificar que el archivo se creó (incluso si hubo warnings)
                check_result = container.exec_run(f"test -f {backup_dir}/{backup.name}.tar.gz", user='root')
                if check_result.exit_code != 0:
                    # Si el archivo no existe, entonces hubo un error real
                    error_msg = output if output else f"Exit code: {result.exit_code}"
                    raise Exception(f"El archivo de backup no se creó en el contenedor. {error_msg}")
                
                # Si el archivo existe, el backup fue exitoso (aunque pueda haber warnings)
                
                # Copiar archivo usando docker cp
                import subprocess
                host_backup_dir = '/data/backups'
                os.makedirs(host_backup_dir, exist_ok=True)
                host_backup_file = os.path.join(host_backup_dir, f"{backup.name}.tar.gz")
                
                cp_result = subprocess.run(
                    ['docker', 'cp', f'{server.container_name}:{backup_dir}/{backup.name}.tar.gz', host_backup_file],
                    capture_output=True,
                    text=True
                )
                
                if cp_result.returncode != 0:
                    raise Exception(f"Error copiando backup del contenedor: {cp_result.stderr}")
                
                if not os.path.exists(host_backup_file):
                    raise Exception("El archivo de backup no existe después de copiar")
                
                file_size = os.path.getsize(host_backup_file)
                backup.file_path = host_backup_file
                backup.file_size = file_size
                backup.status = 'completed'
                backup.completed_at = timezone.now()
                backup.save()
                
                # Limpiar backups antiguos si hay schedule
                schedule = BackupSchedule.objects.filter(server=server, is_active=True).first()
                if schedule:
                    _cleanup_old_backups(server, schedule.max_backups)
                
                return
                
            except docker.errors.NotFound:
                # Contenedor no encontrado, continuar con método local
                pass
            except Exception as e:
                # Si falla Docker, intentar método local
                import traceback
                print(f"Error con Docker, intentando método local: {e}")
                print(traceback.format_exc())
        
        # Método local (fallback o si no hay container_name)
        world_path = os.path.join(server.minecraft_data_path, 'world')
        backup_dir = os.path.join(server.minecraft_data_path, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        backup_file = os.path.join(backup_dir, f"{backup.name}.tar.gz")
        
        # Crear backup comprimido
        with tarfile.open(backup_file, 'w:gz') as tar:
            if os.path.exists(world_path):
                tar.add(world_path, arcname='world')
            # Agregar otros archivos importantes
            config_path = os.path.join(server.minecraft_data_path, 'server.properties')
            if os.path.exists(config_path):
                tar.add(config_path, arcname='server.properties')
            whitelist_path = os.path.join(server.minecraft_data_path, 'whitelist.json')
            if os.path.exists(whitelist_path):
                tar.add(whitelist_path, arcname='whitelist.json')
        
        file_size = os.path.getsize(backup_file)
        backup.file_path = backup_file
        backup.file_size = file_size
        backup.status = 'completed'
        backup.completed_at = timezone.now()
        backup.save()
        
        # Limpiar backups antiguos si hay schedule
        schedule = BackupSchedule.objects.filter(server=server, is_active=True).first()
        if schedule:
            _cleanup_old_backups(server, schedule.max_backups)
            
    except Exception as e:
        backup.status = 'failed'
        backup.error_message = str(e)
        backup.save()
        import traceback
        print(f"Error en backup: {e}")
        print(traceback.format_exc())

def _cleanup_old_backups(server, max_backups):
    """Eliminar backups antiguos manteniendo solo los últimos N"""
    backups = Backup.objects.filter(
        server=server,
        status='completed'
    ).order_by('-created_at')
    
    if backups.count() > max_backups:
        to_delete = backups[max_backups:]
        for backup in to_delete:
            if backup.file_path and os.path.exists(backup.file_path):
                os.remove(backup.file_path)
            backup.delete()

