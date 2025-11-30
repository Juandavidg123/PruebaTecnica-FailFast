from rest_framework import serializers
from .models import Entity
from apps.companies.serializers import CompanySerializer


class EntitySerializer(serializers.ModelSerializer):
    """Serializer para el modelo Entity."""
    company_detail = CompanySerializer(source='company', read_only=True)
    entity_type_display = serializers.CharField(source='get_entity_type_display', read_only=True)

    class Meta:
        model = Entity
        fields = [
            'id', 'company', 'company_detail', 'entity_type', 'entity_type_display',
            'entity_code', 'entity_name', 'metadata', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def validate(self, data):
        """Validar que el código de entidad sea único para la combinación empresa-tipo."""
        company = data.get('company')
        entity_type = data.get('entity_type')
        entity_code = data.get('entity_code')

        if self.instance:
            if Entity.objects.filter(
                company=company,
                entity_type=entity_type,
                entity_code=entity_code
            ).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(
                    f"Ya existe una entidad de tipo {entity_type} con el código {entity_code} en esta empresa"
                )
        else:
            if Entity.objects.filter(
                company=company,
                entity_type=entity_type,
                entity_code=entity_code
            ).exists():
                raise serializers.ValidationError(
                    f"Ya existe una entidad de tipo {entity_type} con el código {entity_code} en esta empresa"
                )

        return data
