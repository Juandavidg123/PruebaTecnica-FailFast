"""
Serializers for Document Management System.
"""
from rest_framework import serializers
from .models import DocumentType, Document, DocumentValidationLog
from apps.companies.serializers import CompanySerializer
from apps.entities.serializers import EntitySerializer


class DocumentTypeSerializer(serializers.ModelSerializer):
    """Serializer para DocumentType."""
    entity_type_display = serializers.CharField(source='get_entity_type_display', read_only=True)

    class Meta:
        model = DocumentType
        fields = [
            'id', 'code', 'name', 'is_mandatory', 'requires_issue_date',
            'requires_expiration_date', 'uses_n8n_workflow', 'n8n_webhook_url',
            'entity_type', 'entity_type_display', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def validate(self, data):
        """Validar que si usa N8N tenga webhook URL."""
        if data.get('uses_n8n_workflow') and not data.get('n8n_webhook_url'):
            raise serializers.ValidationError(
                "Si el documento usa N8N, debe proporcionar la URL del webhook"
            )
        return data


class DocumentValidationLogSerializer(serializers.ModelSerializer):
    """Serializer para DocumentValidationLog."""
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = DocumentValidationLog
        fields = [
            'id', 'document', 'action', 'action_display', 'previous_status',
            'new_status', 'reason', 'performed_by', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer para Document."""
    company_detail = CompanySerializer(source='company', read_only=True)
    entity_detail = EntitySerializer(source='entity', read_only=True)
    document_type_detail = DocumentTypeSerializer(source='document_type', read_only=True)
    validation_status_display = serializers.CharField(source='get_validation_status_display', read_only=True)
    validation_logs = DocumentValidationLogSerializer(many=True, read_only=True)

    class Meta:
        model = Document
        fields = [
            'id', 'company', 'company_detail', 'entity', 'entity_detail',
            'document_type', 'document_type_detail', 'file_name', 'file_size',
            'mime_type', 's3_bucket', 's3_key', 's3_region', 'issue_date',
            'expiration_date', 'validation_status', 'validation_status_display',
            'validation_reason', 'uploaded_by', 'uploaded_at', 'validated_at',
            'validation_logs'
        ]
        read_only_fields = [
            'id', 'file_name', 'file_size', 'mime_type', 's3_bucket', 's3_key',
            's3_region', 'validation_status', 'validation_reason', 'uploaded_at',
            'validated_at'
        ]


class DocumentUploadSerializer(serializers.Serializer):
    """Serializer para cargar documentos."""
    company_id = serializers.UUIDField()
    entity_id = serializers.UUIDField()
    document_type_id = serializers.UUIDField()
    file = serializers.FileField()
    issue_date = serializers.DateField(required=False, allow_null=True)
    expiration_date = serializers.DateField(required=False, allow_null=True)
    uploaded_by = serializers.CharField(max_length=255, required=False, default='system')

    def validate(self, data):
        """Validaciones personalizadas."""
        from apps.companies.models import Company
        from apps.entities.models import Entity
        from .utils import validate_file_size, validate_file_type

        # Validar que existan los objetos
        try:
            company = Company.objects.get(id=data['company_id'])
            if not company.is_active:
                raise serializers.ValidationError("La empresa no está activa")
        except Company.DoesNotExist:
            raise serializers.ValidationError("La empresa no existe")

        try:
            entity = Entity.objects.get(id=data['entity_id'])
            if entity.company_id != data['company_id']:
                raise serializers.ValidationError("La entidad no pertenece a la empresa especificada")
            if not entity.is_active:
                raise serializers.ValidationError("La entidad no está activa")
        except Entity.DoesNotExist:
            raise serializers.ValidationError("La entidad no existe")

        try:
            doc_type = DocumentType.objects.get(id=data['document_type_id'])
            if doc_type.entity_type != entity.entity_type:
                raise serializers.ValidationError(
                    f"El tipo de documento {doc_type.code} no aplica para entidades de tipo {entity.entity_type}"
                )
        except DocumentType.DoesNotExist:
            raise serializers.ValidationError("El tipo de documento no existe")

        # Validar archivo
        try:
            validate_file_size(data['file'])
            validate_file_type(data['file'])
        except ValueError as e:
            raise serializers.ValidationError(str(e))

        # Validar fechas según tipo de documento
        if doc_type.requires_issue_date and not data.get('issue_date'):
            raise serializers.ValidationError(
                f"El tipo de documento {doc_type.code} requiere fecha de emisión"
            )

        if doc_type.requires_expiration_date and not data.get('expiration_date'):
            raise serializers.ValidationError(
                f"El tipo de documento {doc_type.code} requiere fecha de vencimiento"
            )

        # Guardar objetos en el context para no tener que volver a consultarlos
        data['_company'] = company
        data['_entity'] = entity
        data['_document_type'] = doc_type

        return data


class DocumentApproveRejectSerializer(serializers.Serializer):
    """Serializer para aprobar/rechazar documentos."""
    reason = serializers.CharField(required=True)
    performed_by = serializers.CharField(max_length=255, required=False, default='system')


class N8NCallbackSerializer(serializers.Serializer):
    """Serializer para callbacks de N8N."""
    status = serializers.ChoiceField(choices=['approved', 'rejected'])
    reason = serializers.CharField(required=True)
    metadata = serializers.JSONField(required=False, default=dict)


class DocumentValidateSerializer(serializers.Serializer):
    """Serializer para validación masiva."""
    company_id = serializers.UUIDField()
    entity_type = serializers.ChoiceField(
        choices=['vehicle', 'employee', 'supplier', 'asset']
    )
    entity_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_null=True,
        allow_empty=True
    )
