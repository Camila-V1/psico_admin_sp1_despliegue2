# apps/payment_system/serializers.py
import stripe
from rest_framework import serializers
from django.conf import settings
from .models import PaymentTransaction
from apps.appointments.models import Appointment

class PaymentTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar el historial de pagos de un paciente.
    """
    # Añadimos campos legibles desde la cita relacionada
    psychologist_name = serializers.CharField(source='appointment.psychologist.get_full_name', read_only=True)
    appointment_date = serializers.DateField(source='appointment.appointment_date', read_only=True)
    appointment_time = serializers.TimeField(source='appointment.start_time', read_only=True)

    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 
            'appointment_date',
            'appointment_time',
            'psychologist_name', 
            'amount', 
            'currency', 
            'status', 
            'paid_at', 
            'stripe_session_id'
        ]
        read_only_fields = fields # Este endpoint es solo de lectura

class PaymentConfirmationSerializer(serializers.Serializer):
    """
    Serializer para confirmar un pago usando el ID de la sesión de Stripe.
    """
    session_id = serializers.CharField(max_length=255)

    def validate(self, data):
        session_id = data.get('session_id')
        
        try:
            # 1. Validamos la sesión con Stripe
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status != 'paid':
                raise serializers.ValidationError("El pago no ha sido completado.")
            
            # 2. Obtenemos la cita de los metadatos
            metadata = session.get('metadata', {})
            appointment_id = metadata.get('appointment_id')
            if not appointment_id:
                raise serializers.ValidationError("ID de cita no encontrado en la sesión de Stripe.")
            
            # 3. Buscamos la cita en nuestra BD
            appointment = Appointment.objects.get(id=appointment_id)
            
            # 4. ¡LA CLAVE! Guardamos todo en validated_data para que la vista lo use
            data['stripe_session'] = session
            data['appointment'] = appointment
            
            return data
        
        except Appointment.DoesNotExist:
            raise serializers.ValidationError("La cita asociada a este pago no fue encontrada.")
        except stripe.error.StripeError as e:
            raise serializers.ValidationError(f"Error de Stripe: {str(e)}")
        except Exception as e:
            raise serializers.ValidationError(f"Error validando la sesión: {str(e)}")