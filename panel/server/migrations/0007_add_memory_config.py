# Generated migration for memory configuration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0006_add_mods_pool'),
    ]

    operations = [
        migrations.AddField(
            model_name='server',
            name='memory_limit_mb',
            field=models.IntegerField(
                default=2048,
                help_text='Límite de memoria RAM en MB (ej: 2048 = 2GB)'
            ),
        ),
        migrations.AddField(
            model_name='server',
            name='java_heap_min_mb',
            field=models.IntegerField(
                default=512,
                help_text='Heap mínimo de Java en MB (Xms)'
            ),
        ),
        migrations.AddField(
            model_name='server',
            name='java_heap_max_mb',
            field=models.IntegerField(
                default=1536,
                help_text='Heap máximo de Java en MB (Xmx) - debe ser < memory_limit_mb'
            ),
        ),
        migrations.AddField(
            model_name='server',
            name='java_gc_type',
            field=models.CharField(
                choices=[
                    ('g1', 'G1GC (recomendado para >2GB)'),
                    ('parallel', 'ParallelGC (para <2GB)'),
                    ('zgc', 'ZGC (experimental, Java 17+)'),
                ],
                default='g1',
                help_text='Tipo de Garbage Collector',
                max_length=20
            ),
        ),
    ]






