# apps/clinical_history/views.py

import logging
import os
from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404
from django.conf import settings
from .models import SessionNote, ClinicalDocument, ClinicalHistory, InitialTriage, MoodJournal  # <-- IMPORTA ClinicalHistory
from .serializers import SessionNoteSerializer, ClinicalDocumentSerializer, PsychologistPatientSerializer, ClinicalHistorySerializer, InitialTriageSubmitSerializer, MoodJournalSerializer  # <-- IMPORTA ClinicalHistorySerializer
from apps.appointments.models import Appointment
from apps.users.models import CustomUser
from datetime import date


logger = logging.getLogger(__name__)

class IsAssociatedProfessional(permissions.BasePermission):
    """
    Permiso personalizado para asegurar que solo el psicólogo de la cita
    pueda acceder a la nota.
    """
    def has_permission(self, request, view):
        # Solo los usuarios tipo 'professional' pueden acceder.
        if request.user.user_type != 'professional':
            return False
        
        # Obtenemos el ID de la cita desde la URL.
        appointment_id = view.kwargs.get('appointment_pk')
        try:
            appointment = Appointment.objects.get(pk=appointment_id)
            # Verificamos si el usuario actual es el psicólogo de esa cita.
            return request.user == appointment.psychologist
        except Appointment.DoesNotExist:
            return False

class SessionNoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para crear y gestionar notas de sesión.
    Accesible a través de /api/appointments/appointments/<appointment_pk>/note/
    """
    serializer_class = SessionNoteSerializer
    permission_classes = [permissions.IsAuthenticated, IsAssociatedProfessional]

    def get_queryset(self):
        # Este ViewSet solo se usa para una cita específica, no para listar todas.
        appointment_id = self.kwargs.get('appointment_pk')
        return SessionNote.objects.filter(appointment_id=appointment_id)

    def perform_create(self, serializer):
        # Asignamos la cita automáticamente desde la URL.
        appointment_id = self.kwargs.get('appointment_pk')
        appointment = Appointment.objects.get(pk=appointment_id)
        serializer.save(appointment=appointment)

    def create(self, request, *args, **kwargs):
        # Prevenimos que se cree más de una nota por cita.
        appointment_id = self.kwargs.get('appointment_pk')
        if SessionNote.objects.filter(appointment_id=appointment_id).exists():
            return Response(
                {"error": "Ya existe una nota para esta cita."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        Obtener la nota de la cita específica (debería ser máximo 1)
        """
        queryset = self.get_queryset()
        if queryset.exists():
            serializer = self.get_serializer(queryset.first())
            return Response(serializer.data)
        else:
            return Response(
                {"message": "No hay nota para esta cita"},
                status=status.HTTP_404_NOT_FOUND
            )


# --- NUEVAS VISTAS PARA DOCUMENTOS CLÍNICOS ---

class MyDocumentsListView(generics.ListAPIView):
    """
    Endpoint para que un paciente vea todos los documentos que le han subido.
    (CU-39 - Vista del Paciente)
    """
    serializer_class = ClinicalDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Solo mostrar si el usuario es paciente
        if self.request.user.user_type != 'patient':
            return ClinicalDocument.objects.none()
        
        # Devuelve solo los documentos del usuario autenticado
        return ClinicalDocument.objects.filter(patient=self.request.user)


class MyPastPatientsListView(generics.ListAPIView):
    """
    Endpoint para que un psicólogo obtenga una lista de todos los pacientes
    con los que ha tenido una cita.
    (CU-39 - Vista del Psicólogo para seleccionar paciente)
    """
    serializer_class = PsychologistPatientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Solo mostrar si el usuario es psicólogo
        if self.request.user.user_type != 'professional':
            return CustomUser.objects.none()
            
        psychologist = self.request.user
        # Obtiene los IDs de todos los pacientes que han tenido una cita con el psicólogo
        patient_ids = Appointment.objects.filter(psychologist=psychologist)\
                                         .values_list('patient_id', flat=True)\
                                         .distinct()
        # Devuelve la lista de esos usuarios
        return CustomUser.objects.filter(id__in=patient_ids)


class DocumentUploadView(generics.CreateAPIView):
    """
    Endpoint para que un psicólogo suba un documento a un paciente específico.
    (CU-39 - Acción de Subir)
    """
    serializer_class = ClinicalDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Asigna al psicólogo actual como la persona que sube el archivo
        serializer.save(uploaded_by=self.request.user)

    def create(self, request, *args, **kwargs):
        # Solo psicólogos pueden subir documentos
        if request.user.user_type != 'professional':
            return Response(
                {"error": "Solo los psicólogos pueden subir documentos."},
                status=status.HTTP_403_FORBIDDEN
            )

        # --- Validación de Permiso Clave ---
        # Verifica si el psicólogo tiene permiso para subir archivos a este paciente
        patient_id = request.data.get('patient')
        if not patient_id:
            return Response(
                {"error": "Debe especificar un paciente."},
                status=status.HTTP_400_BAD_REQUEST
            )

        psychologist = request.user

        has_had_appointment = Appointment.objects.filter(
            psychologist=psychologist,
            patient_id=patient_id
        ).exists()

        if not has_had_appointment:
            return Response(
                {"error": "No tienes permiso para subir documentos a este paciente. Solo puedes subir documentos a pacientes con los que has tenido una cita."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)


# --- 👇 AÑADE ESTE NUEVO CÓDIGO AL FINAL DEL ARCHIVO 👇 ---

class IsOwnerOrAssociatedProfessional(permissions.BasePermission):
    """
    Permiso para permitir el acceso al historial clínico solo al propio paciente
    o a un profesional que haya tenido al menos una cita con ese paciente.
    """
    def has_permission(self, request, view):
        patient_id = view.kwargs.get('patient_id')
        user = request.user

        if not user.is_authenticated:
            return False

        # El paciente puede ver su propio historial
        if user.id == patient_id and user.user_type == 'patient':
            return True

        # El profesional puede acceder si ha tenido una cita con el paciente
        if user.user_type == 'professional':
            has_appointment = Appointment.objects.filter(
                psychologist=user,
                patient_id=patient_id
            ).exists()
            return has_appointment

        return False


class ClinicalHistoryDetailView(generics.RetrieveUpdateAPIView):
    """
    Vista para obtener y actualizar el historial clínico de un paciente.
    Maneja la creación si el historial no existe.
    """
    queryset = ClinicalHistory.objects.all()
    serializer_class = ClinicalHistorySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAssociatedProfessional]
    lookup_field = 'patient_id'

    def get_object(self):
        # Obtener el historial. Si no existe, se crea uno nuevo vacío.
        patient_id = self.kwargs.get('patient_id')
        patient = get_object_or_404(CustomUser, id=patient_id, user_type='patient')

        history, created = ClinicalHistory.objects.get_or_create(
            patient=patient,
            defaults={'created_by': self.request.user}  # Asigna quien lo creó por primera vez
        )
        return history

    def perform_update(self, serializer):
        # Asigna automáticamente al profesional que está realizando la última actualización.
        logger.info(f"📝 [ClinicalHistory] Usuario {self.request.user.id} actualizando historia clínica del paciente {self.kwargs.get('patient_id')}")
        logger.debug(f"   Campos recibidos: {serializer.validated_data.keys()}")
        logger.debug(f"   Valores: {serializer.validated_data}")
        serializer.save(last_updated_by=self.request.user)
        logger.info(f"✅ [ClinicalHistory] Historia clínica actualizada exitosamente")


class DownloadDocumentView(generics.RetrieveAPIView):
    """
    Vista para descargar un documento clínico de forma segura desde S3.
    Solo el paciente dueño o el psicólogo que subió el documento puede descargarlo.
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = ClinicalDocument.objects.all()
    lookup_field = 'pk'

    def retrieve(self, request, *args, **kwargs):
        from django.http import HttpResponse
        from apps.backups.s3_storage import S3BackupStorage
        
        document = self.get_object()
        user = request.user

        logger.info(f"🔍 [Download] Solicitud de descarga - Doc ID: {document.id}, Usuario: {user.id} ({user.email})")
        logger.info(f"   Documento: {document.description}")
        logger.info(f"   Archivo field: {document.file}")
        logger.info(f"   Archivo name: {document.file.name}")
        logger.info(f"   Paciente ID: {document.patient.id}, Subido por: {document.uploaded_by.id}")

        # Verificar permisos: el paciente dueño o el profesional que lo subió
        if user.id != document.patient.id and user.id != document.uploaded_by.id:
            logger.warning(f"❌ [Download] Usuario {user.id} intentó descargar documento {document.id} sin permiso")
            return Response(
                {"error": "No tienes permiso para descargar este documento."},
                status=status.HTTP_403_FORBIDDEN
            )

        logger.info(f"✅ [Download] Permisos OK")

        # Descargar desde S3
        try:
            s3_storage = S3BackupStorage()
            file_content = s3_storage.download_file(document.file.name)
            
            logger.info(f"✅ [Download] Archivo descargado desde S3, enviando respuesta")
            
            # Determinar content type
            content_type = 'application/octet-stream'
            if document.file.name.endswith('.pdf'):
                content_type = 'application/pdf'
            elif document.file.name.endswith('.png'):
                content_type = 'image/png'
            elif document.file.name.endswith(('.jpg', '.jpeg')):
                content_type = 'image/jpeg'
            
            response = HttpResponse(file_content, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(document.file.name)}"'
            return response
            
        except Exception as e:
            logger.error(f"❌ [Download] Error al descargar desde S3: {e}")
            raise Http404(f"Archivo no encontrado en S3: {str(e)}")

# apps/clinical_history/views.py
# ... (después de la clase DownloadDocumentView) ...

class IsPatient(permissions.BasePermission):
    """Permiso para asegurar que el usuario sea un paciente."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'patient'

class InitialTriageView(generics.GenericAPIView):
    """
    Endpoint para que un paciente envíe (POST) o consulte (GET)
    su triaje inicial (CU-21).
    """
    permission_classes = [IsPatient]
    serializer_class = InitialTriageSubmitSerializer

    def get(self, request, *args, **kwargs):
        """Obtener el resultado del triaje si ya existe"""
        try:
            triage = InitialTriage.objects.get(patient=request.user)
            # Usamos el serializer para mostrar los datos (sin 'answers')
            serializer = self.get_serializer(triage)
            return Response(serializer.data)
        except InitialTriage.DoesNotExist:
            return Response(
                {"error": "El paciente aún no ha completado el triaje inicial."},
                status=status.HTTP_404_NOT_FOUND
            )

    def post(self, request, *args, **kwargs):
        """Enviar las respuestas del triaje"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            triage_result = serializer.save()
            # Devolvemos el objeto completo (incluyendo el diagnóstico)
            return Response(
                InitialTriageSubmitSerializer(triage_result).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MoodJournalView(generics.ListCreateAPIView):
    """
    Endpoint para que un paciente CREE (POST) su entrada de ánimo del día
    o VEA (GET) su historial de entradas.
    """
    serializer_class = MoodJournalSerializer
    permission_classes = [IsPatient] # Reutilizamos el permiso de Paciente

    def get_queryset(self):
        """Sobrescribimos para devolver solo el historial del paciente logueado."""
        return MoodJournal.objects.filter(patient=self.request.user)

    def perform_create(self, serializer):
        """Sobrescribimos para asignar al paciente y la fecha automáticamente."""
        serializer.save(patient=self.request.user, date=date.today())


class TodayMoodJournalView(generics.RetrieveAPIView):
    """
    Endpoint especial para que el frontend verifique (GET)
    si el paciente ya registró su ánimo HOY.
    """
    serializer_class = MoodJournalSerializer
    permission_classes = [IsPatient]

    def get_object(self):
        """
        Intenta obtener el registro de hoy.
        Si no lo encuentra, lanza un 404, que es lo que el frontend
        usará para saber que debe mostrar el popup.
        """
        return get_object_or_404(
            MoodJournal, 
            patient=self.request.user, 
            date=date.today()
        )