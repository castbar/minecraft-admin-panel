from django.db import models

class MinecraftVersion(models.Model):
    """Versiones de Minecraft disponibles para servidores"""
    version = models.CharField(
        max_length=20,
        unique=True,
        help_text="Versión de Minecraft (ej: 1.20.1, 1.19.4)"
    )
    display_name = models.CharField(
        max_length=50,
        help_text="Nombre para mostrar (ej: 1.20.1 - Latest)"
    )
    is_latest = models.BooleanField(
        default=False,
        help_text="¿Es la versión más reciente?"
    )
    is_stable = models.BooleanField(
        default=True,
        help_text="¿Es una versión estable?"
    )
    is_supported = models.BooleanField(
        default=True,
        help_text="¿Está soportada actualmente?"
    )
    server_types = models.JSONField(
        default=list,
        help_text="Tipos de servidor compatibles: ['vanilla', 'fabric', 'forge', 'bukkit', 'spigot', 'paper']"
    )
    release_date = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha de lanzamiento"
    )
    notes = models.TextField(
        blank=True,
        help_text="Notas sobre esta versión"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_latest', '-version']
        verbose_name = "Versión de Minecraft"
        verbose_name_plural = "Versiones de Minecraft"
    
    def __str__(self):
        return f"{self.display_name} ({self.version})"
    
    @classmethod
    def get_available_versions(cls, server_type=None):
        """Obtener versiones disponibles, opcionalmente filtradas por tipo de servidor"""
        queryset = cls.objects.filter(is_supported=True)
        
        if server_type:
            queryset = queryset.filter(
                models.Q(server_types__contains=[server_type]) | 
                models.Q(server_types=[])
            )
        
        return queryset
    
    @classmethod
    def get_latest_version(cls, server_type=None):
        """Obtener la versión más reciente"""
        versions = cls.get_available_versions(server_type)
        latest = versions.filter(is_latest=True).first()
        if not latest:
            # Si no hay marcada como latest, devolver la más reciente por fecha
            latest = versions.order_by('-release_date', '-version').first()
        return latest

