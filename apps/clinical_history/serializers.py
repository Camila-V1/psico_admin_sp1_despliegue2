# apps/clinical_history/serializers.py

from rest_framework import serializers
from .models import SessionNote, ClinicalDocument, ClinicalHistory  # <-- 1. IMPORTA EL NUEVO MODELO
from apps.users.models import CustomUser

class SessionNoteSerializer(serializers.ModelSerializer):
    # Información adicional de la cita para el frontend
    appointment_date = serializers.DateField(source='appointment.appointment_date', read_only=True)
    appointment_time = serializers.TimeField(source='appointment.start_time', read_only=True)
    patient_name = serializers.CharField(source='appointment.patient.get_full_name', read_only=True)
    
    class Meta:
        model = SessionNote
        fields = [
            'id',
            'appointment',
            'content',
            'created_at',
            'updated_at',
            # Campos adicionales para el frontend
            'appointment_date',
            'appointment_time', 
            'patient_name'
        ]
        # Hacemos que 'appointment' sea de solo lectura porque lo obtendremos de la URL.
        read_only_fields = ['appointment', 'appointment_date', 'appointment_time', 'patient_name']

    def validate_content(self, value):
        """Validar que el contenido no esté vacío"""
        if not value.strip():
            raise serializers.ValidationError("El contenido de la nota no puede estar vacío")
        return value.strip()


class ClinicalDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    file_url = serializers.SerializerMethodField()
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)

    class Meta:
        model = ClinicalDocument
        fields = [
            'id',
            'patient',
            'patient_name',
            'uploaded_by',
            'uploaded_by_name',
            'file',
            'file_url',
            'description',
            'uploaded_at'
        ]
        read_only_fields = ['uploaded_by', 'uploaded_by_name', 'file_url', 'uploaded_at', 'patient_name']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None

    def validate_description(self, value):
        """Validar que la descripción no esté vacía"""
        if not value.strip():
            raise serializers.ValidationError("La descripción del documento no puede estar vacía")
        return value.strip()


class PsychologistPatientSerializer(serializers.ModelSerializer):
    """Serializer simple para listar los pacientes de un psicólogo."""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'full_name', 'email']


# --- 👇 AÑADE ESTA NUEVA CLASE AL FINAL DEL ARCHIVO 👇 ---

class ClinicalHistorySerializer(serializers.ModelSerializer):
    """
    Serializer para leer y escribir en el modelo de Historial Clínico.
    """
    class Meta:
        model = ClinicalHistory
        # Incluimos todos los campos que definimos en el modelo
        fields = [
            'patient',
            'consultation_reason',
            'history_of_illness',
            'personal_pathological_history',
            'family_history',
            'personal_non_pathological_history',
            'mental_examination',
            'complementary_tests',
            'diagnoses',
            'therapeutic_plan',
            'risk_assessment',
            'sensitive_topics',
            'created_by',
            'last_updated_by',
            'created_at',
            'updated_at',
        ]
        # Hacemos que ciertos campos sean de solo lectura para proteger los datos
        read_only_fields = ['patient', 'created_by', 'created_at', 'updated_at']