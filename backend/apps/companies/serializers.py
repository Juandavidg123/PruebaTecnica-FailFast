from rest_framework import serializers
from .models import Company


class CompanySerializer(serializers.ModelSerializer):
    """Serializer para el modelo Company."""

    class Meta:
        model = Company
        fields = ['id', 'name', 'tax_id', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_tax_id(self, value):
        """Validar formato del NIT."""
        if not value or len(value) < 5:
            raise serializers.ValidationError("El NIT debe tener al menos 5 caracteres")
        return value
