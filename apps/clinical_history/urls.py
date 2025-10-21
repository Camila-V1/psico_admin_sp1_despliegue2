# apps/clinical_history/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # --- (Tus URLs existentes no cambian) ---
    path('my-documents/', views.MyDocumentsListView.as_view(), name='my-documents'),
    path('my-patients/', views.MyPastPatientsListView.as_view(), name='my-past-patients'),
    path('documents/upload/', views.DocumentUploadView.as_view(), name='document-upload'),
    path('documents/<int:pk>/download/', views.DownloadDocumentView.as_view(), name='document-download'),

    # --- 👇 AÑADE ESTA NUEVA LÍNEA 👇 ---
    path('patient/<int:patient_id>/', views.ClinicalHistoryDetailView.as_view(), name='clinical-history-detail'),
]