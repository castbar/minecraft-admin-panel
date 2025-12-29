#!/usr/bin/env python
"""Script para crear superusuario"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'minecraft_panel.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'change-me-in-production')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f'Superusuario creado: {username}')
else:
    print(f'Superusuario {username} ya existe')

