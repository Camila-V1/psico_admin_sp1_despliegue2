#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🔧 Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🗄️ Aplicando migraciones al esquema público..."
python manage.py migrate_schemas --shared

echo "📁 Recolectando archivos estáticos..."
python manage.py collectstatic --no-input

echo "✅ Build completado!"
