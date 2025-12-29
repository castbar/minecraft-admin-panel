from django.core.management.base import BaseCommand
from django.utils import timezone
from server.models import BackupSchedule, Backup
from server.views_backup import _execute_backup
from datetime import datetime, time

class Command(BaseCommand):
    help = 'Ejecutar backups programados'

    def handle(self, *args, **options):
        now = timezone.now()
        schedules = BackupSchedule.objects.filter(is_active=True)
        
        for schedule in schedules:
            if self._should_run(schedule, now):
                self.stdout.write(f'Ejecutando backup: {schedule.name} para {schedule.server.name}')
                
                backup_name = f"{schedule.name}_{now.strftime('%Y%m%d_%H%M%S')}"
                backup = Backup.objects.create(
                    server=schedule.server,
                    name=backup_name,
                    status='pending'
                )
                
                _execute_backup(backup.id)
                schedule.last_run = now
                schedule.save()
                
                self.stdout.write(self.style.SUCCESS(f'Backup {backup.name} iniciado'))

    def _should_run(self, schedule, now):
        """Verificar si el schedule debe ejecutarse"""
        if not schedule.last_run:
            # Primera ejecución
            if schedule.frequency == 'hourly':
                return True
            elif schedule.frequency == 'daily':
                return now.time() >= schedule.time
            # ... más lógica para weekly/monthly
            return False
        
        time_since_last = now - schedule.last_run
        
        if schedule.frequency == 'hourly':
            return time_since_last.total_seconds() >= 3600
        elif schedule.frequency == 'daily':
            return (time_since_last.days >= 1 and 
                   now.time() >= schedule.time)
        elif schedule.frequency == 'weekly':
            return (time_since_last.days >= 7 and
                   now.weekday() == schedule.day_of_week and
                   now.time() >= schedule.time)
        elif schedule.frequency == 'monthly':
            return (time_since_last.days >= 28 and
                   now.day == schedule.day_of_month and
                   now.time() >= schedule.time)
        
        return False

