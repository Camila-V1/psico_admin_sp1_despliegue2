"""
Comando de Django para configurar tenants de demostración en Render.
Se ejecuta automáticamente durante el build.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.tenants.models import Clinic, Domain


class Command(BaseCommand):
    help = 'Crea las clínicas Bienestar y Mindcare para demostración'

    def handle(self, *args, **options):
        self.stdout.write("🏥 Configurando clínicas de demostración...")
        
        # Verificar si ya existen
        if Clinic.objects.filter(schema_name='bienestar').exists():
            self.stdout.write(self.style.WARNING('⚠️ Clínica Bienestar ya existe'))
        else:
            # Crear clínica Bienestar
            bienestar = Clinic.objects.create(
                schema_name='bienestar',
                name='Clínica Bienestar',
                paid_until=timezone.now().date() + timedelta(days=365),
                on_trial=False
            )
            Domain.objects.create(
                domain='bienestar.psico-admin.onrender.com',
                tenant=bienestar,
                is_primary=True
            )
            self.stdout.write(self.style.SUCCESS(f'✅ Clínica Bienestar creada: {bienestar.schema_name}'))
        
        if Clinic.objects.filter(schema_name='mindcare').exists():
            self.stdout.write(self.style.WARNING('⚠️ Clínica Mindcare ya existe'))
        else:
            # Crear clínica Mindcare
            mindcare = Clinic.objects.create(
                schema_name='mindcare',
                name='Clínica Mindcare',
                paid_until=timezone.now().date() + timedelta(days=365),
                on_trial=False
            )
            Domain.objects.create(
                domain='mindcare.psico-admin.onrender.com',
                tenant=mindcare,
                is_primary=True
            )
            self.stdout.write(self.style.SUCCESS(f'✅ Clínica Mindcare creada: {mindcare.schema_name}'))
        
        # Aplicar migraciones a los tenants
        self.stdout.write("📊 Aplicando migraciones a los tenants...")
        from django.core.management import call_command
        call_command('migrate_schemas', verbosity=0)
        
        self.stdout.write(self.style.SUCCESS('\n🎉 ¡Clínicas configuradas exitosamente!'))
        self.stdout.write(self.style.SUCCESS('📍 Bienestar: https://bienestar.psico-admin.onrender.com'))
        self.stdout.write(self.style.SUCCESS('📍 Mindcare: https://mindcare.psico-admin.onrender.com'))
