"""
Modelos para soporte multi-servidor y sesiones guardadas
"""
from django.db import models
from django.contrib.auth.models import User

class ServerSession(models.Model):
    """Sesiones guardadas de servidores para usuarios"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='server_sessions')
    server = models.ForeignKey('server.Server', on_delete=models.CASCADE, related_name='sessions')
    last_accessed = models.DateTimeField(auto_now=True)
    is_favorite = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'server']
        ordering = ['-last_accessed']
        indexes = [
            models.Index(fields=['user', 'last_accessed']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.server.name}"

class UserPreference(models.Model):
    """Preferencias del usuario para el panel"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    default_server = models.ForeignKey(
        'server.Server', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='default_for_users'
    )
    theme = models.CharField(
        max_length=20, 
        choices=[('light', 'Claro'), ('dark', 'Oscuro')], 
        default='light'
    )
    language = models.CharField(max_length=10, default='es')
    notifications_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Preferences for {self.user.username}"

