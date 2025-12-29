from django.db import models

# Server se importa después para evitar circular import

class Backup(models.Model):
    """Backups del servidor Minecraft"""
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('running', 'Ejecutando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
    ]
    
    server = models.ForeignKey('server.Server', on_delete=models.CASCADE, related_name='backups')
    name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500, null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)  # Tamaño en bytes
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadatos
    world_size = models.BigIntegerField(null=True, blank=True)
    player_count = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['server', 'status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.server.name} - {self.name} ({self.status})"
    
    def get_file_size_mb(self):
        """Obtener tamaño en MB"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0

class BackupSchedule(models.Model):
    """Programación de backups automáticos"""
    FREQUENCY_CHOICES = [
        ('hourly', 'Cada hora'),
        ('daily', 'Diario'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual'),
    ]
    
    server = models.ForeignKey('server.Server', on_delete=models.CASCADE, related_name='backup_schedules')
    name = models.CharField(max_length=100)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='daily')
    time = models.TimeField(help_text="Hora de ejecución (para daily/weekly/monthly)")
    day_of_week = models.IntegerField(null=True, blank=True, help_text="Día de la semana (0=Lunes, 6=Domingo)")
    day_of_month = models.IntegerField(null=True, blank=True, help_text="Día del mes (1-31)")
    is_active = models.BooleanField(default=True)
    max_backups = models.IntegerField(default=10, help_text="Máximo de backups a mantener")
    storage_type = models.CharField(max_length=20, choices=[('local', 'Local'), ('s3', 'S3')], default='local')
    s3_bucket = models.CharField(max_length=255, null=True, blank=True)
    s3_path = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_run = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['server', 'name']

    def __str__(self):
        return f"{self.server.name} - {self.name} ({self.frequency})"

