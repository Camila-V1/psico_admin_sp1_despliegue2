# apps/professionals/views.py

import logging
from rest_framework import status, permissions, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import ProfessionalProfile, Specialization, Review
from .serializers import (
    ProfessionalProfileSerializer,
    ProfessionalProfileUpdateSerializer,
    ProfessionalPublicSerializer,
    SpecializationSerializer,
    ReviewSerializer
)
from apps.appointments.models import Appointment

logger = logging.getLogger(__name__)
User = get_user_model()

@api_view(['GET', 'POST', 'PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def professional_profile_detail(request):
    """
    CU-06: Completar Perfil Profesional
    Solo psicólogos y admins pueden gestionar perfiles profesionales
    """
    user = request.user
    
    # Verificar permisos
    if user.user_type not in ['professional', 'admin']:
        return Response({
            'error': 'Solo psicólogos y administradores pueden acceder'
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        try:
            if user.user_type == 'admin':
                # Admin puede ver cualquier perfil (requiere ID en query params)
                prof_id = request.query_params.get('professional_id')
                if prof_id:
                    professional = get_object_or_404(
                        User.objects.filter(user_type='professional'), 
                        id=prof_id
                    )
                    profile = professional.professional_profile
                else:
                    return Response({
                        'error': 'professional_id requerido para admin'
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Psicólogo ve su propio perfil
                profile = user.professional_profile
            
            serializer = ProfessionalProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except ProfessionalProfile.DoesNotExist:
            return Response({
                'message': 'Perfil profesional no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
    
    elif request.method == 'POST':
        # Crear perfil profesional
        if user.user_type != 'professional':
            return Response({
                'error': 'Solo psicólogos pueden crear perfil profesional'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if hasattr(user, 'professional_profile'):
            return Response({
                'error': 'Ya tienes un perfil profesional'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ProfessionalProfileUpdateSerializer(data=request.data)
        if serializer.is_valid():
            profile = serializer.save(user=user)
            response_serializer = ProfessionalProfileSerializer(profile)
            return Response({
                'message': 'Perfil profesional creado exitosamente',
                'profile': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method in ['PUT', 'PATCH']:
        # Actualizar perfil profesional
        try:
            if user.user_type == 'admin':
                prof_id = request.data.get('professional_id')
                if prof_id:
                    professional = get_object_or_404(
                        User.objects.filter(user_type='professional'), 
                        id=prof_id
                    )
                    profile = professional.professional_profile
                else:
                    return Response({
                        'error': 'professional_id requerido para admin'
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                profile = user.professional_profile
            
            partial = request.method == 'PATCH'
            serializer = ProfessionalProfileUpdateSerializer(
                profile, data=request.data, partial=partial
            )
            
            if serializer.is_valid():
                serializer.save()
                response_serializer = ProfessionalProfileSerializer(profile)
                return Response({
                    'message': 'Perfil actualizado exitosamente',
                    'profile': response_serializer.data
                }, status=status.HTTP_200_OK)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except ProfessionalProfile.DoesNotExist:
            return Response({
                'error': 'Perfil profesional no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def list_professionals(request):
    """
    CU-08: Buscar y Filtrar Profesionales
    """
    logger.info(f"🔍 [Professionals] Listando profesionales - Parámetros: {request.query_params.dict()}")
    
    # Filtros disponibles
    specialization = request.query_params.get('specialization')
    city = request.query_params.get('city')
    max_fee = request.query_params.get('max_fee')
    min_rating = request.query_params.get('min_rating')
    accepts_online = request.query_params.get('accepts_online')
    search = request.query_params.get('search')
    
    # Query base: solo perfiles activos (quitamos is_verified para testing)
    profiles = ProfessionalProfile.objects.filter(
        is_active=True,
        profile_completed=True
    )
    logger.debug(f"   Perfiles base (activos + completados): {profiles.count()}")
    
    # Aplicar filtros
    if specialization:
        profiles = profiles.filter(specializations__name__icontains=specialization)
        logger.debug(f"   Después de filtro especialización: {profiles.count()}")
    
    if city:
        profiles = profiles.filter(city__icontains=city)
        logger.debug(f"   Después de filtro ciudad: {profiles.count()}")
    
    if max_fee:
        try:
            profiles = profiles.filter(consultation_fee__lte=float(max_fee))
            logger.debug(f"   Después de filtro tarifa máxima: {profiles.count()}")
        except ValueError:
            logger.warning(f"   ⚠️ Valor inválido para max_fee: {max_fee}")
            pass
    
    if min_rating:
        try:
            profiles = profiles.filter(average_rating__gte=float(min_rating))
            logger.debug(f"   Después de filtro rating mínimo: {profiles.count()}")
        except ValueError:
            logger.warning(f"   ⚠️ Valor inválido para min_rating: {min_rating}")
            pass
    
    if accepts_online:
        profiles = profiles.filter(accepts_online_sessions=True)
        logger.debug(f"   Después de filtro sesiones online: {profiles.count()}")
    
    if search:
        profiles = profiles.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search)
        )
        logger.debug(f"   Después de búsqueda por nombre: {profiles.count()}")
    
    serializer = ProfessionalPublicSerializer(profiles, many=True)
    logger.info(f"✅ [Professionals] Retornando {profiles.count()} profesionales")
    
    return Response({
        'count': profiles.count(),
        'professionals': serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def professional_public_detail(request, professional_id):
    """
    CU-09: Ver Perfil Público Profesional
    Vista pública de un psicólogo específico
    """
    try:
        profile = get_object_or_404(
            ProfessionalProfile.objects.filter(
                is_active=True,
                profile_completed=True
            ),
            id=professional_id
        )
        
        serializer = ProfessionalPublicSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except ProfessionalProfile.DoesNotExist:
        return Response({
            'error': 'Profesional no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def list_specializations(request):
    """
    Listar todas las especialidades disponibles
    """
    specializations = Specialization.objects.all()
    serializer = SpecializationSerializer(specializations, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


class CanReviewAppointment(permissions.BasePermission):
    """
    Permiso para asegurar que un paciente solo pueda calificar una cita
    que le pertenece y que ya ha sido completada.
    """
    def has_permission(self, request, view):
        if request.user.user_type != 'patient':
            return False
        
        appointment_id = request.data.get('appointment')
        try:
            appointment = Appointment.objects.get(pk=appointment_id)
            # 1. La cita debe pertenecer al paciente que hace la petición.
            # 2. El estado de la cita debe ser 'completed'.
            # 3. La cita no debe tener ya una reseña.
            return (appointment.patient == request.user and 
                    appointment.status == 'completed' and 
                    not hasattr(appointment, 'review'))
        except Appointment.DoesNotExist:
            return False


class ReviewCreateView(generics.CreateAPIView):
    """
    Endpoint para que un paciente cree una reseña para una cita completada.
    (CU-34)
    """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated, CanReviewAppointment]

    def perform_create(self, serializer):
        appointment = Appointment.objects.get(pk=self.request.data.get('appointment'))
        # Asignar el paciente y el profesional automáticamente
        serializer.save(
            patient=self.request.user, 
            professional=appointment.psychologist.professional_profile
        )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def professional_reviews(request, professional_id):
    """
    Lista las reseñas de un profesional específico (vista pública)
    """
    try:
        professional = get_object_or_404(ProfessionalProfile, id=professional_id)
        reviews = Review.objects.filter(professional=professional).order_by('-created_at')
        serializer = ReviewSerializer(reviews, many=True)
        return Response({
            'professional_id': professional_id,
            'total_reviews': reviews.count(),
            'average_rating': professional.average_rating,
            'reviews': serializer.data
        }, status=status.HTTP_200_OK)
        
    except ProfessionalProfile.DoesNotExist:
        return Response({
            'error': 'Profesional no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)