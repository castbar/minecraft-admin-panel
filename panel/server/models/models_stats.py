from django.db import models


class ServerStatistic(models.Model):
    """Estadísticas del servidor en tiempo real"""
    server = models.ForeignKey('server.Server', on_delete=models.CASCADE, related_name='statistics')
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Jugadores
    players_online = models.IntegerField(default=0)
    players_max = models.IntegerField(default=0)
    
    # Recursos
    cpu_usage = models.FloatField(null=True, blank=True)  # Porcentaje
    memory_usage = models.BigIntegerField(null=True, blank=True)  # Bytes
    memory_max = models.BigIntegerField(null=True, blank=True)  # Bytes
    disk_usage = models.BigIntegerField(null=True, blank=True)  # Bytes
    disk_total = models.BigIntegerField(null=True, blank=True)  # Bytes
    
    # Red
    latency = models.FloatField(null=True, blank=True)  # ms
    network_in = models.BigIntegerField(null=True, blank=True)  # Bytes
    network_out = models.BigIntegerField(null=True, blank=True)  # Bytes
    
    # TPS (Ticks Per Second)
    tps = models.FloatField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['server', 'timestamp']),
        ]
        get_latest_by = 'timestamp'

    def __str__(self):
        return f"{self.server.name} - {self.timestamp} ({self.players_online} players)"

class ServerEvent(models.Model):
    """Eventos importantes del servidor"""
    EVENT_TYPES = [
        ('player_join', 'Jugador conectado'),
        ('player_leave', 'Jugador desconectado'),
        ('server_start', 'Servidor iniciado'),
        ('server_stop', 'Servidor detenido'),
        ('server_crash', 'Servidor crasheado'),
        ('backup_completed', 'Backup completado'),
        ('backup_failed', 'Backup fallido'),
        ('plugin_enabled', 'Plugin habilitado'),
        ('plugin_disabled', 'Plugin deshabilitado'),
        ('warning', 'Advertencia'),
        ('error', 'Error'),
    ]
    
    server = models.ForeignKey('server.Server', on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    message = models.TextField()
    player_name = models.CharField(max_length=16, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['server', 'event_type', 'created_at']),
        ]

    def __str__(self):
        return f"{self.server.name} - {self.get_event_type_display()} - {self.created_at}"

