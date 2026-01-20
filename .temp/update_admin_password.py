#!/usr/bin/env python
"""Script temporal para actualizar contraseña del administrador"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'minecraft_panel.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Nueva contraseña segura
NEW_PASSWORD = 'hpI#QjOa@ts689Pu$8WSrJD3'

# Buscar usuario admin
admin = User.objects.filter(username='admin').first()
if not admin:
    admin = User.objects.filter(is_superuser=True).first()

if admin:
    admin.set_password(NEW_PASSWORD)
    admin.save()
    print(f'✅ Contraseña actualizada para usuario: {admin.username}')
    print(f'📧 Email: {admin.email}')
    print(f'🔑 Nueva contraseña: {NEW_PASSWORD}')
else:
    print('❌ No se encontró usuario administrador')
    print('💡 Creando nuevo superusuario...')
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@castbar.dev',
        password=NEW_PASSWORD
    )
    print(f'✅ Superusuario creado: {admin.username}')
    print(f'🔑 Contraseña: {NEW_PASSWORD}')
