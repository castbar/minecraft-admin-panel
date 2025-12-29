from django.db import models


class IPWhitelist(models.Model):
    """Lista blanca de IPs permitidas"""
    server = models.ForeignKey('server.Server', on_delete=models.CASCADE, related_name='ip_whitelist')
    ip_address = models.GenericIPAddressField()
    description = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ['server', 'ip_address']
        indexes = [
            models.Index(fields=['server', 'ip_address']),
        ]

    def __str__(self):
        return f"{self.server.name} - {self.ip_address}"

class IPBlacklist(models.Model):
    """Lista negra de IPs bloqueadas"""
    server = models.ForeignKey('server.Server', on_delete=models.CASCADE, related_name='ip_blacklist')
    ip_address = models.GenericIPAddressField()
    reason = models.TextField(null=True, blank=True)
    is_permanent = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ['server', 'ip_address']
        indexes = [
            models.Index(fields=['server', 'ip_address', 'expires_at']),
        ]

    def __str__(self):
        return f"{self.server.name} - {self.ip_address} ({'Permanente' if self.is_permanent else 'Temporal'})"
    
    def is_active(self):
        """Verificar si el bloqueo está activo"""
        if self.is_permanent:
            return True
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() < self.expires_at
        return True

class RateLimitRule(models.Model):
    """Reglas de rate limiting"""
    server = models.ForeignKey('server.Server', on_delete=models.CASCADE, related_name='rate_limit_rules')
    action = models.CharField(max_length=50, help_text="Acción a limitar (ej: login, command)")
    max_requests = models.IntegerField(default=10)
    time_window = models.IntegerField(default=60, help_text="Ventana de tiempo en segundos")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['server', 'action']

    def __str__(self):
        return f"{self.server.name} - {self.action} ({self.max_requests}/{self.time_window}s)"

class SecurityLog(models.Model):
    """Logs de seguridad"""
    LOG_TYPES = [
        ('failed_login', 'Login fallido'),
        ('successful_login', 'Login exitoso'),
        ('suspicious_activity', 'Actividad sospechosa'),
        ('rate_limit_exceeded', 'Rate limit excedido'),
        ('ip_blocked', 'IP bloqueada'),
        ('unauthorized_access', 'Acceso no autorizado'),
    ]
    
    server = models.ForeignKey('server.Server', on_delete=models.CASCADE, related_name='security_logs', null=True, blank=True)
    log_type = models.CharField(max_length=50, choices=LOG_TYPES)
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=500, null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['server', 'log_type', 'created_at']),
            models.Index(fields=['ip_address', 'created_at']),
        ]

    def __str__(self):
        return f"{self.get_log_type_display()} - {self.ip_address} - {self.created_at}"

