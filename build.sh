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

echo "🏥 Creando clínicas de demostración..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.tenants.models import Clinic, Domain

# Crear Bienestar si no existe
if not Clinic.objects.filter(schema_name='bienestar').exists():
    bienestar = Clinic.objects.create(
        schema_name='bienestar',
        name='Clínica Bienestar'
    )
    Domain.objects.create(
        domain='bienestar.psico-admin.onrender.com',
        tenant=bienestar,
        is_primary=True
    )
    print('✅ Clínica Bienestar creada')
else:
    print('⚠️ Clínica Bienestar ya existe')

# Crear Mindcare si no existe
if not Clinic.objects.filter(schema_name='mindcare').exists():
    mindcare = Clinic.objects.create(
        schema_name='mindcare',
        name='Clínica Mindcare'
    )
    Domain.objects.create(
        domain='mindcare.psico-admin.onrender.com',
        tenant=mindcare,
        is_primary=True
    )
    print('✅ Clínica Mindcare creada')
else:
    print('⚠️ Clínica Mindcare ya existe')

print('🎉 Clínicas configuradas')
"

echo "📊 Aplicando migraciones a los tenants..."
python manage.py migrate_schemas || echo "⚠️ Error en migraciones de tenants"

echo "✅ Build completado!"
