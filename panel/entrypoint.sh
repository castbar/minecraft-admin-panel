#!/bin/bash
set -e

echo "🚀 Iniciando panel Django..."

# Esperar un momento para que la base de datos esté lista
sleep 2

# Ejecutar migraciones
echo "📦 Ejecutando migraciones..."
python manage.py migrate --noinput

# Recolectar archivos estáticos
echo "📁 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

# Crear superusuario si no existe (solo si no hay usuarios)
echo "👤 Verificando superusuario..."
python create_superuser.py || echo "⚠️  Error al crear superusuario, puede que ya exista"

# Iniciar servidor
echo "✅ Iniciando servidor Django..."
exec python manage.py runserver 0.0.0.0:8000

