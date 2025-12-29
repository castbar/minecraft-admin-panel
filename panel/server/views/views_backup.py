from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
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
def backup_schedules_list(request, server_id):
    """Listar programaciones de backups"""
    server = request.server
    schedules = BackupSchedule.objects.filter(server=server)
    
    data = [{
        'id': s.id,
        'name': s.name,
        'frequency': s.frequency,
        'time': s.time.strftime('%H:%M') if s.time else None,
        'is_active': s.is_active,
        'max_backups': s.max_backups,
        'last_run': s.last_run.isoformat() if s.last_run else None,
    } for s in schedules]
    
    return JsonResponse({'success': True, 'data': data})

def _execute_backup(backup_id):
    """Ejecutar backup en background"""
    try:
        backup = Backup.objects.get(id=backup_id)
        backup.status = 'running'
        backup.save()
        
        server = backup.server
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

