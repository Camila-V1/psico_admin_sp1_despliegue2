# apps/tenants/urls.py

from django.urls import path
from .views import (
    ClinicListCreateView, 
    ClinicDetailView, 
    global_admin_stats, 
    clinic_detail_stats
)

app_name = 'tenants'

urlpatterns = [
    path('clinics/', ClinicListCreateView.as_view(), name='clinic-list-create'),
    path('clinics/<int:pk>/', ClinicDetailView.as_view(), name='clinic-detail'),
    path('admin/stats/', global_admin_stats, name='global-admin-stats'),
    path('clinics/<int:clinic_id>/stats/', clinic_detail_stats, name='clinic-detail-stats'),
]