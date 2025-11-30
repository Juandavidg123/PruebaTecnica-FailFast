from django.contrib import admin
from .models import DocumentType, Document, DocumentValidationLog


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'entity_type', 'is_mandatory', 'uses_n8n_workflow', 'created_at']
    list_filter = ['entity_type', 'is_mandatory', 'uses_n8n_workflow']
    search_fields = ['code', 'name']
    readonly_fields = ['id', 'created_at']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'document_type', 'entity', 'validation_status', 'uploaded_at', 'expiration_date']
    list_filter = ['validation_status', 'document_type', 'uploaded_at']
    search_fields = ['file_name', 'entity__entity_code', 'entity__entity_name']
    readonly_fields = ['id', 'uploaded_at', 'validated_at', 's3_bucket', 's3_key', 's3_region']
    autocomplete_fields = ['company', 'entity', 'document_type']
    date_hierarchy = 'uploaded_at'


@admin.register(DocumentValidationLog)
class DocumentValidationLogAdmin(admin.ModelAdmin):
    list_display = ['document', 'action', 'previous_status', 'new_status', 'performed_by', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['document__file_name', 'performed_by']
    readonly_fields = ['id', 'created_at']
    autocomplete_fields = ['document']
    date_hierarchy = 'created_at'
