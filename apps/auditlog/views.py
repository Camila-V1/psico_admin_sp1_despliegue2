# apps/auditlog/views.py
from rest_framework import viewsets, permissions
from django.db.models import Q
from .models import LogEntry
from .serializers import LogEntrySerializer
from apps.clinic_admin.permissions import IsClinicAdmin

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para que los administradores de la clínica
    vean los registros de la bitácora.
    """
    serializer_class = LogEntrySerializer
    permission_classes = [permissions.IsAuthenticated, IsClinicAdmin]

    def get_queryset(self):
        queryset = LogEntry.objects.all().order_by('-timestamp')

        # --- Lógica de filtrado en el servidor ---
        level = self.request.query_params.get('level')
        search = self.request.query_params.get('search')

        if level:
            queryset = queryset.filter(level__iexact=level)

        if search:
            queryset = queryset.filter(
                Q(action__icontains=search) |
                Q(user__email__icontains=search) |
                Q(ip_address__icontains=search)
            )

        return queryset
