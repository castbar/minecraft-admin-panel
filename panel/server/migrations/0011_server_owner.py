# Generated migration for adding owner field to Server

from django.conf import settings
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('server', '0010_server_port'),
    ]

    operations = [
        migrations.AddField(
            model_name='server',
            name='owner',
            field=models.ForeignKey(
                help_text='Usuario propietario del servidor',
                null=True,  # Permitir null temporalmente para migración
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='owned_servers',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        # Migración de datos: asignar servidores existentes al primer superuser
        migrations.RunPython(
            code=lambda apps, schema_editor: _assign_servers_to_superuser(apps, schema_editor),
            reverse_code=migrations.RunPython.noop,
        ),
        # Hacer el campo requerido después de migrar datos
        migrations.AlterField(
            model_name='server',
            name='owner',
            field=models.ForeignKey(
                help_text='Usuario propietario del servidor',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='owned_servers',
                to=settings.AUTH_USER_MODEL
            ),
        ),
    ]


def _assign_servers_to_superuser(apps, schema_editor):
    """Asignar servidores existentes al primer superuser"""
    Server = apps.get_model('server', 'Server')
    User = apps.get_model('auth', 'User')
    
    # Obtener primer superuser o crear uno si no existe
    superuser = User.objects.filter(is_superuser=True).first()
    if not superuser:
        # Si no hay superuser, usar el primer usuario activo
        superuser = User.objects.filter(is_active=True).first()
    
    if superuser:
        # Asignar todos los servidores sin owner al superuser
        Server.objects.filter(owner__isnull=True).update(owner=superuser)
        print(f"✅ Servidores sin propietario asignados a: {superuser.username}")
    else:
        print("⚠️ No se encontró ningún usuario para asignar servidores")
