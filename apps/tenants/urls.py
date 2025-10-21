# apps/tenants/urls.py

from django.urls import path
from .views import (
    ClinicListCreateView, 
    ClinicDetailView, 
    global_admin_stats, 
    clinic_detail_stats,
    register_tenant,  # ⭐ NUEVO
    check_subdomain_availability  # ⭐ NUEVO
)

app_name = 'tenants'

urlpatterns = [
    # Endpoints protegidos (requieren autenticación)
    path('clinics/', ClinicListCreateView.as_view(), name='clinic-list-create'),
    path('clinics/<int:pk>/', ClinicDetailView.as_view(), name='clinic-detail'),
    path('admin/stats/', global_admin_stats, name='global-admin-stats'),
    path('clinics/<int:clinic_id>/stats/', clinic_detail_stats, name='clinic-detail-stats'),
    
    # ⭐ Endpoints públicos (NO requieren autenticación)
    path('public/register/', register_tenant, name='register-tenant'),
    path('public/check-subdomain/', check_subdomain_availability, name='check-subdomain'),
]