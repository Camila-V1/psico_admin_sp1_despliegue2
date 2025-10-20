# apps/backups/urls.py

from django.urls import path
from .views import CreateBackupAndDownloadView, RestoreBackupFromFileView

urlpatterns = [
    path('create/', CreateBackupAndDownloadView.as_view(), name='create-backup'),
    path('restore/', RestoreBackupFromFileView.as_view(), name='restore-backup'),
]