# config/urls.py
# Rutas para los tenants (clínicas individuales)

from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from config.admin_site import tenant_admin_site

urlpatterns = [
    # Admin ESPECÍFICO para tenants (sin gestión de clínicas)
    path('admin/', tenant_admin_site.urls),

    # Todas las rutas de la API para cada clínica
    path('api/auth/', include('apps.authentication.urls')),      # CU-01, CU-02, CU-03, CU-04
    path('api/users/', include('apps.users.urls')),              # CU-05
    path('api/professionals/', include('apps.professionals.urls')), # CU-06, CU-08, CU-09, CU-12
    path('api/appointments/', include('apps.appointments.urls')), # CU-10 ⭐ ESTA ES LA CLAVE
    path('api/clinical-history/', include('apps.clinical_history.urls')), # CU-18, CU-39
    path('api/admin/', include('apps.clinic_admin.urls')),  # CU-30, CU-07 gestión interna de usuarios y verificación
    path('api/payments/', include('apps.payment_system.urls')),  # Sistema de pagos con Stripe
    path('api/chat/', include('apps.chat.urls')),           # Chat por WebSocket
    path('api/backups/', include('apps.backups.urls')),     # Sistema de backups
    path('api/auditlog/', include('apps.auditlog.urls')),   # 👈 NUEVA: Sistema de bitácora
    
    # API browsable (para desarrollo)
    path('api-auth/', include('rest_framework.urls')),
]

# Servir archivos media y static en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)