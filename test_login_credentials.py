#!/usr/bin/env python
"""
Script para probar login con las credenciales creadas
Ejecutar en Render Shell: python test_login_credentials.py
"""

import os
import django
import requests
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model, authenticate
from django_tenants.utils import schema_context
from apps.tenants.models import Clinic

User = get_user_model()

def test_direct_authentication():
    """Probar autenticación directa en Django"""
    print("\n" + "="*70)
    print("🔐 PRUEBA DE AUTENTICACIÓN DIRECTA")
    print("="*70)
    
    test_credentials = [
        ('bienestar', 'admin@bienestar.com', 'admin123'),
        ('bienestar', 'juan.perez@example.com', 'demo123'),
        ('mindcare', 'admin@mindcare.com', 'admin123'),
        ('mindcare', 'carlos.ruiz@example.com', 'demo123'),
    ]
    
    for schema, email, password in test_credentials:
        print(f"\n{'─'*70}")
        print(f"🏥 Tenant: {schema}")
        print(f"📧 Email: {email}")
        print(f"🔑 Password: {password}")
        
        clinic = Clinic.objects.get(schema_name=schema)
        
        with schema_context(schema):
            # Verificar si el usuario existe
            try:
                user = User.objects.get(email=email)
                print(f"✅ Usuario encontrado: {user.username}")
                print(f"   Tipo: {user.user_type}")
                print(f"   Activo: {user.is_active}")
                print(f"   Staff: {user.is_staff}")
                
                # Probar check_password
                if user.check_password(password):
                    print(f"✅ Contraseña correcta")
                else:
                    print(f"❌ Contraseña incorrecta")
                    
                # Probar authenticate
                auth_user = authenticate(username=email, password=password)
                if auth_user:
                    print(f"✅ Autenticación exitosa con authenticate()")
                else:
                    print(f"❌ Autenticación falló con authenticate()")
                    
            except User.DoesNotExist:
                print(f"❌ Usuario NO encontrado en la BD")

def test_api_endpoint():
    """Probar el endpoint de login vía HTTP"""
    print("\n" + "="*70)
    print("🌐 PRUEBA DE ENDPOINT DE LOGIN")
    print("="*70)
    
    test_cases = [
        {
            'url': 'https://bienestar.psicoadmin.xyz/api/auth/login/',
            'data': {'email': 'admin@bienestar.com', 'password': 'admin123'},
            'tenant': 'bienestar'
        },
        {
            'url': 'https://bienestar.psicoadmin.xyz/api/auth/login/',
            'data': {'email': 'juan.perez@example.com', 'password': 'demo123'},
            'tenant': 'bienestar'
        },
    ]
    
    for test in test_cases:
        print(f"\n{'─'*70}")
        print(f"🌐 URL: {test['url']}")
        print(f"📧 Email: {test['data']['email']}")
        print(f"🔑 Password: {test['data']['password']}")
        
        try:
            response = requests.post(
                test['url'],
                json=test['data'],
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            print(f"📊 Status Code: {response.status_code}")
            print(f"📄 Response:")
            try:
                print(json.dumps(response.json(), indent=2))
            except:
                print(response.text)
                
        except Exception as e:
            print(f"❌ Error: {e}")

def check_user_fields():
    """Verificar campos de usuario para debug"""
    print("\n" + "="*70)
    print("🔍 VERIFICACIÓN DE CAMPOS DE USUARIO")
    print("="*70)
    
    with schema_context('bienestar'):
        try:
            user = User.objects.get(email='admin@bienestar.com')
            print(f"\n✅ Usuario encontrado: admin@bienestar.com")
            print(f"   ID: {user.id}")
            print(f"   Username: {user.username}")
            print(f"   Email: {user.email}")
            print(f"   First name: {user.first_name}")
            print(f"   Last name: {user.last_name}")
            print(f"   User type: {user.user_type}")
            print(f"   Is active: {user.is_active}")
            print(f"   Is staff: {user.is_staff}")
            print(f"   Is superuser: {user.is_superuser}")
            print(f"   Password hash: {user.password[:20]}...")
            print(f"   Date joined: {user.date_joined}")
            
            # Verificar que check_password funciona
            test_password = 'admin123'
            if user.check_password(test_password):
                print(f"\n✅ check_password('{test_password}') = True")
            else:
                print(f"\n❌ check_password('{test_password}') = False")
                print(f"   ⚠️ La contraseña NO coincide!")
                
        except User.DoesNotExist:
            print(f"❌ Usuario admin@bienestar.com NO existe")

def main():
    print("\n🔬 DIAGNÓSTICO COMPLETO DE LOGIN")
    print("📅 Fecha: 2025-10-21")
    print("="*70)
    
    # 1. Verificar campos
    check_user_fields()
    
    # 2. Probar autenticación directa
    test_direct_authentication()
    
    # 3. Probar endpoint HTTP (solo si estamos en Render)
    # test_api_endpoint()  # Comentado porque necesita acceso a internet
    
    print("\n" + "="*70)
    print("✅ DIAGNÓSTICO COMPLETADO")
    print("="*70)
    print("\n💡 Si check_password = False:")
    print("   La contraseña no se guardó correctamente")
    print("   Solución: Recrear el usuario con set_password()")
    print("\n💡 Si authenticate() falla:")
    print("   Problema con TenantAwareAuthBackend")
    print("   Verificar settings.AUTHENTICATION_BACKENDS")
    print()

if __name__ == '__main__':
    main()
