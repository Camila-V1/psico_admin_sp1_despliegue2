# apps/tenants/serializers.py

from rest_framework import serializers
from .models import Clinic, Domain

class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ['domain', 'is_primary']

class ClinicSerializer(serializers.ModelSerializer):
    domains = DomainSerializer(many=True, read_only=True)
    
    class Meta:
        model = Clinic
        fields = ['id', 'name', 'schema_name', 'created_on', 'domains']
        read_only_fields = ['created_on', 'domains']

class ClinicCreateSerializer(serializers.ModelSerializer):
    domain = serializers.CharField(write_only=True, help_text="Dominio principal para la clínica")
    
    class Meta:
        model = Clinic
        fields = ['name', 'schema_name', 'domain']
    
    def validate_schema_name(self, value):
        """Validar que el schema_name sea válido"""
        if not value.isalnum():
            raise serializers.ValidationError("El nombre del esquema debe contener solo letras y números")
        if value in ['public', 'postgres', 'information_schema']:
            raise serializers.ValidationError("El nombre del esquema no puede ser una palabra reservada")
        return value.lower()
    
    def validate_domain(self, value):
        """Validar que el dominio no esté en uso"""
        if Domain.objects.filter(domain=value).exists():
            raise serializers.ValidationError("Este dominio ya está en uso")
        return value
    
    def create(self, validated_data):
        domain_name = validated_data.pop('domain')
        clinic = Clinic.objects.create(**validated_data)
        
        # Crear el dominio asociado
        Domain.objects.create(
            domain=domain_name,
            tenant=clinic,
            is_primary=True
        )
        
        return clinic