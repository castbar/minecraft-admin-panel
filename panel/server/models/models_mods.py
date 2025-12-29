"""
Modelos para gestión de configuraciones de mods
"""
from django.db import models
from django.contrib.auth.models import User
import json

class ModConfigTemplate(models.Model):
    """
    Plantilla de configuración global para un mod
    Cada mod puede tener una plantilla con valores por defecto
    """
    CONFIG_FORMAT_CHOICES = [
        ('json', 'JSON'),
        ('yaml', 'YAML'),
        ('properties', 'Properties'),
        ('toml', 'TOML'),
        ('txt', 'Texto plano'),
    ]
    
    mod_name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Nombre del mod (ej: 'cobblemon', 'jei', 'wthit')"
    )
    display_name = models.CharField(
        max_length=255,
        help_text="Nombre para mostrar (ej: 'Cobblemon', 'JEI', 'WTHIT')"
    )
    config_format = models.CharField(
        max_length=20,
        choices=CONFIG_FORMAT_CHOICES,
        default='json',
        help_text="Formato del archivo de configuración"
    )
    config_file_path = models.CharField(
        max_length=500,
        help_text="Ruta relativa del archivo de configuración (ej: 'config/cobblemon.json', 'config/jei/jei-client.toml')"
    )
    default_config = models.TextField(
        blank=True,
        help_text="Configuración por defecto (contenido del archivo)"
    )
    description = models.TextField(
        blank=True,
        help_text="Descripción del mod y su configuración"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="¿Está activa esta plantilla?"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Plantilla de Configuración de Mod"
        verbose_name_plural = "Plantillas de Configuración de Mods"
        ordering = ['display_name']
    
    def __str__(self):
        return f"{self.display_name} ({self.mod_name})"
    
    def get_config_dict(self):
        """Obtener configuración como diccionario (si es JSON)"""
        if self.config_format == 'json' and self.default_config:
            try:
                return json.loads(self.default_config)
            except json.JSONDecodeError:
                return {}
        return {}

class ServerModConfig(models.Model):
    """
    Configuración específica de un mod para un servidor
    Permite personalizar la configuración por servidor
    """
    server = models.ForeignKey(
        'server.Server',
        on_delete=models.CASCADE,
        related_name='mod_configs'
    )
    mod_template = models.ForeignKey(
        ModConfigTemplate,
        on_delete=models.CASCADE,
        related_name='server_configs'
    )
    config_content = models.TextField(
        blank=True,
        help_text="Configuración personalizada para este servidor (si está vacío, usa la plantilla)"
    )
    is_enabled = models.BooleanField(
        default=True,
        help_text="¿Está habilitada esta configuración en el servidor?"
    )
    last_applied = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Última vez que se aplicó esta configuración al servidor"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_mod_configs'
    )
    
    class Meta:
        unique_together = ['server', 'mod_template']
        verbose_name = "Configuración de Mod por Servidor"
        verbose_name_plural = "Configuraciones de Mods por Servidor"
        ordering = ['server', 'mod_template__display_name']
    
    def __str__(self):
        return f"{self.server.name} - {self.mod_template.display_name}"
    
    def get_config_content(self):
        """Obtener contenido de configuración (personalizado o de plantilla)"""
        if self.config_content:
            return self.config_content
        return self.mod_template.default_config
    
    def get_config_dict(self):
        """Obtener configuración como diccionario (si es JSON)"""
        content = self.get_config_content()
        if self.mod_template.config_format == 'json' and content:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def apply_to_server(self):
        """
        Aplicar configuración al servidor (escribir archivo)
        Retorna True si se aplicó correctamente
        """
        if not self.is_enabled:
            return False
        
        try:
            import os
            config_content = self.get_config_content()
            if not config_content:
                return False
            
            # Construir ruta completa del archivo
            config_file_path = os.path.join(
                self.server.minecraft_data_path,
                self.mod_template.config_file_path
            )
            
            # Crear directorio si no existe
            config_dir = os.path.dirname(config_file_path)
            os.makedirs(config_dir, exist_ok=True)
            
            # Escribir archivo
            with open(config_file_path, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            # Actualizar timestamp
            from django.utils import timezone
            self.last_applied = timezone.now()
            self.save(update_fields=['last_applied'])
            
            return True
        except Exception as e:
            print(f"Error aplicando configuración de mod: {e}")
            return False

