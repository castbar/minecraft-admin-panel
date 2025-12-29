from django.db import models
from django.contrib.auth.models import User


class Ticket(models.Model):
    """Sistema de tickets/soporte"""
    STATUS_CHOICES = [
        ('open', 'Abierto'),
        ('in_progress', 'En progreso'),
        ('resolved', 'Resuelto'),
        ('closed', 'Cerrado'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]
    
    server = models.ForeignKey('server.Server', on_delete=models.CASCADE, related_name='tickets')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tickets')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['server', 'status', 'priority']),
        ]

    def __str__(self):
        return f"{self.server.name} - {self.title} ({self.status})"

class TicketComment(models.Model):
    """Comentarios en tickets"""
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_internal = models.BooleanField(default=False, help_text="Comentario interno (no visible para el creador)")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment on {self.ticket.title} by {self.author.username}"

class PlayerRanking(models.Model):
    """Ranking de jugadores"""
    server = models.ForeignKey('server.Server', on_delete=models.CASCADE, related_name='rankings')
    player_name = models.CharField(max_length=16, db_index=True)
    metric = models.CharField(max_length=50, help_text="Métrica (ej: playtime, deaths, kills)")
    value = models.FloatField()
    rank = models.IntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['server', 'player_name', 'metric']
        indexes = [
            models.Index(fields=['server', 'metric', 'value']),
        ]

    def __str__(self):
        return f"{self.server.name} - {self.player_name} ({self.metric}: {self.value})"

