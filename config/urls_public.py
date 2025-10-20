# config/urls_public.py
# Rutas para el tenant público (admin de tenants)

from django.urls import path, include  
from config.admin_site import public_admin_site

urlpatterns = [
    # Admin público para gestión de clínicas/tenants
    path('admin/', public_admin_site.urls),
    
    # ⚠️ IMPORTANTE: Rutas de pagos disponibles en dominio público para webhooks de Stripe
    path('api/payments/', include('apps.payment_system.urls')),  # Sistema de pagos con Stripe
    
    # 🔧 RUTAS ADICIONALES PARA EL TENANT PÚBLICO:
    # Permitir autenticación básica en el tenant público (útil para admin)
    path('api/auth/', include('apps.authentication.urls')),      # Autenticación básica
    
    # API para gestión de clínicas/tenants
    path('api/tenants/', include('apps.tenants.urls')),          # Gestión de clínicas
    
    # API browsable (para desarrollo en tenant público)
    path('api-auth/', include('rest_framework.urls')),
]