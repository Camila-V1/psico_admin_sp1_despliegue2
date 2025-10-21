# apps/authentication/views.py

import logging
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from .serializers import (
    UserRegistrationSerializer, 
    UserLoginSerializer, 
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    ChangePasswordSerializer
)

logger = logging.getLogger(__name__)
User = get_user_model()

@api_view(['POST'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def register_user(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'message': 'Usuario registrado exitosamente',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'user_type': user.user_type,
            },
            'token': token.key
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# apps/authentication/views.py

# ... (otras importaciones y vistas no cambian) ...

# 👇 REEMPLAZA ESTA FUNCIÓN COMPLETA 👇
@api_view(['POST'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def login_user(request):
    logger.info(f"🔐 [Login] Intento de login - Email: {request.data.get('email')}")
    logger.debug(f"   Content-Type: {request.content_type}")
    logger.debug(f"   request.data: {request.data}")
    
    serializer = UserLoginSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = serializer.validated_data['user']
        logger.info(f"✅ [Login] Validación exitosa - Usuario: {user.email} (ID: {user.id})")
        
        # --- INICIO DE LA CORRECCIÓN ---
        # Importamos el modelo PublicUser para poder comprobar de qué tipo es el usuario
        from apps.tenants.models import PublicUser

        # Si el usuario autenticado es una instancia de PublicUser, es el admin global.
        if isinstance(user, PublicUser):
            logger.info(f"👑 [Login] Admin Global detectado - Email: {user.email}")
            # Para el admin global, no generamos un token de API.
            # Su autenticación se maneja por sesiones de Django para el /admin/.
            # Devolvemos una respuesta especial para que el frontend sepa cómo actuar.
            return Response({
                'message': 'Sesión de administrador global iniciada exitosamente.',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'user_type': 'superuser',  # Un tipo especial para que el frontend lo reconozca
                },
                'token': 'global-admin-session' # Enviamos un token simulado
            }, status=status.HTTP_200_OK)
        # --- FIN DE LA CORRECCIÓN ---

        # Si no es un PublicUser, es un CustomUser de una clínica.
        logger.info(f"👤 [Login] Usuario de clínica detectado - Tipo: {user.user_type}")
        # Continuamos con la lógica original de crear un token.
        token, created = Token.objects.get_or_create(user=user)
        logger.debug(f"   Token generado: {token.key[:10]}... (nuevo: {created})")
        
        return Response({
            'message': 'Sesión iniciada exitosamente',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'user_type': user.user_type,
            },
            'token': token.key
        }, status=status.HTTP_200_OK)
        
    # 🔍 DEBUG: Si la validación falla, logueamos los errores
    logger.error(f"❌ [Login] Validación fallida para email: {request.data.get('email')}")
    logger.error(f"   Errores del serializer: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ... (el resto de las vistas no cambian) ...
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_user(request):
    try:
        request.user.auth_token.delete()
        return Response({'message': 'Sesión cerrada exitosamente'}, status=status.HTTP_200_OK)
    except:
        return Response({'error': 'Error al cerrar sesión'}, status=status.HTTP_400_BAD_REQUEST)
# apps/authentication/views.py

# --- 1. AÑADE ESTAS IMPORTACIONES AL INICIO DEL ARCHIVO ---
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import send_mail
# ----------------------------------------------------

# ... (aquí van tus otras vistas: register_user, login_user, etc.) ...


# --- 2. REEMPLAZA TU VISTA password_reset_request CON ESTA ---
@api_view(['POST'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def password_reset_request(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Preparamos el contexto para la plantilla de correo
        context = {
            'email': user.email,
            'user': user,
            'uid': uid,
            'token': token,
            'FRONTEND_URL_LOCAL': settings.FRONTEND_URL_LOCAL, # Usamos la variable de settings.py
        }

        # Renderizamos la plantilla HTML que creamos en el Paso 1
        email_body = render_to_string('registration/password_reset_email.html', context)
        
        # Enviamos el correo
        send_mail(
            subject='Restablecimiento de contraseña para Psico SAS',
            message=email_body, # Usamos el HTML como mensaje (los clientes de correo modernos lo renderizarán)
            from_email=settings.DEFAULT_FROM_EMAIL, # Usará el correo que configuraste
            recipient_list=[user.email],
            html_message=email_body, # Le decimos que es HTML
            fail_silently=False,
        )

        return Response({
            'message': 'Si el correo está registrado, recibirás instrucciones en breve.'
        }, status=status.HTTP_200_OK)
        
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# apps/authentication/views.py

@api_view(['POST'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def password_reset_confirm(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if serializer.is_valid():
        # Obtener TODOS los datos validados del serializer
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        uid = serializer.validated_data['uid'] # <--- LÍNEA CORREGIDA
        
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
            
            if default_token_generator.check_token(user, token):
                user.set_password(new_password)
                user.save()
                return Response({'message': 'Contraseña restablecida exitosamente'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Token inválido'}, status=status.HTTP_400_BAD_REQUEST)
        except:
            # Esto atrapa errores si el uid es inválido (ej. decodificación falla)
            return Response({'error': 'Token inválido'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Si el serializer no es válido, retorna los errores (esto es lo que ves como 400)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        new_password = serializer.validated_data['new_password']
        request.user.set_password(new_password)
        request.user.save()
        
        try:
            request.user.auth_token.delete()
        except:
            pass
        token = Token.objects.create(user=request.user)
        
        return Response({
            'message': 'Contraseña cambiada exitosamente',
            'token': token.key
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_profile(request):
    user = request.user
    return Response({
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'user_type': user.user_type,
        'phone': user.phone,
        'is_verified': user.is_verified,
    }, status=status.HTTP_200_OK)