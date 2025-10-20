# apps/clinical_history/models.py

from django.db import models
from django.conf import settings
from apps.appointments.models import Appointment

class SessionNote(models.Model):
    """
    Modelo para las notas privadas de un profesional sobre una cita específica.
    """
    # Usamos OneToOne para asegurar que solo haya UNA nota por cita.
    appointment = models.OneToOneField(
        Appointment, 
        on_delete=models.CASCADE, 
        related_name='session_note'
    )
    
    content = models.TextField(
        help_text="Notas privadas del profesional sobre la sesión."
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-appointment__appointment_date']
        verbose_name = 'Nota de Sesión'
        verbose_name_plural = 'Notas de Sesión'
        db_table = 'session_notes'

    def __str__(self):
        return f"Nota para la cita del {self.appointment.appointment_date} con {self.appointment.patient.get_full_name()}"


class ClinicalDocument(models.Model):
    """
    Modelo para documentos subidos por un profesional para un paciente específico.
    """
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='clinical_documents',
        limit_choices_to={'user_type': 'patient'}
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Si el psicólogo se elimina, no borramos el documento
        null=True,
        related_name='uploaded_documents',
        limit_choices_to={'user_type': 'professional'}
    )
    
    # El archivo en sí
    file = models.FileField(upload_to='clinical_documents/%Y/%m/%d/')
    
    description = models.CharField(max_length=255, help_text="Descripción o título del documento.")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Documento Clínico'
        verbose_name_plural = 'Documentos Clínicos'
        db_table = 'clinical_documents'

    def __str__(self):
        return f"Documento '{self.description}' para {self.patient.get_full_name()}"


# --- 👇 AÑADIDO: NUEVO MODELO PARA HISTORIAL CLÍNICO COMPLETO 👇 ---

class ClinicalHistory(models.Model):
    """
    Modelo central para almacenar el historial clínico completo de un paciente.
    """
    # --- VÍNCULO CON EL PACIENTE ---
    patient = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='clinical_history',
        limit_choices_to={'user_type': 'patient'},
        primary_key=True # Cada paciente tendrá solo UNA historia clínica
    )

    # --- SECCIONES DEL HISTORIAL ---

    # Motivo e Historia
    consultation_reason = models.TextField(blank=True, help_text="Frase textual del paciente sobre el motivo de consulta.")
    history_of_illness = models.TextField(blank=True, help_text="Relato cronológico de la enfermedad actual (HEA).")

    # Antecedentes
    personal_pathological_history = models.TextField(blank=True, help_text="Enfermedades previas, cirugías, trastornos mentales, etc.")
    family_history = models.TextField(blank=True, help_text="Trastornos mentales, suicidio, adicciones en la familia.")
    personal_non_pathological_history = models.JSONField(default=dict, blank=True, help_text="Hábitos de alimentación, sueño, consumo de sustancias, etc.")

    # Examen / Exploración
    mental_examination = models.JSONField(default=dict, blank=True, help_text="Resultados de la exploración mental (conciencia, orientación, lenguaje, etc.).")
    complementary_tests = models.TextField(blank=True, help_text="Resultados de pruebas de laboratorio, gabinete o psicométricas.")

    # Diagnóstico y Plan
    diagnoses = models.JSONField(default=list, blank=True, help_text="Lista de diagnósticos (principal y secundarios) con códigos CIE-10/DSM-5.")
    therapeutic_plan = models.JSONField(default=dict, blank=True, help_text="Plan farmacológico, psicoterapéutico e intervenciones sociales.")

    # Riesgos y Alertas
    risk_assessment = models.JSONField(default=dict, blank=True, help_text="Evaluación de riesgos (autolesión, heteroagresión, recaída).")
    sensitive_topics = models.TextField(blank=True, help_text="Temas delicados a tratar con cuidado.")

    # --- METADATOS ---
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_histories',
        help_text="Profesional que creó el historial."
    )
    last_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_histories',
        help_text="Último profesional que actualizó el historial."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Historial Clínico'
        verbose_name_plural = 'Historiales Clínicos'

    def __str__(self):
        return f"Historial Clínico de {self.patient.get_full_name()}"
