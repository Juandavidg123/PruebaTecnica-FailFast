"""
Document models for FailFast Document Management System.
"""
import uuid
from django.db import models
from django.core.validators import URLValidator
from apps.companies.models import Company
from apps.entities.models import Entity
from .constants import ValidationStatus, DocumentAction, EntityType


class DocumentType(models.Model):
    """
    Tipo de documento que se puede adjuntar a una entidad.

    Attributes:
        id: Identificador único UUID
        code: Código único del tipo de documento (ej: SOAT, LICENCIA_CONDUCIR)
        name: Nombre descriptivo del tipo de documento
        is_mandatory: Indica si el documento es obligatorio
        requires_issue_date: Indica si requiere fecha de emisión
        requires_expiration_date: Indica si requiere fecha de vencimiento
        uses_n8n_workflow: Indica si usa flujo de trabajo N8N
        n8n_webhook_url: URL del webhook de N8N
        entity_type: Tipo de entidad al que aplica
        created_at: Fecha de creación
    """
    ENTITY_TYPE_CHOICES = EntityType.CHOICES

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True, verbose_name='Código')
    name = models.CharField(max_length=255, verbose_name='Nombre')
    is_mandatory = models.BooleanField(default=False, verbose_name='Obligatorio')
    requires_issue_date = models.BooleanField(default=False, verbose_name='Requiere fecha de emisión')
    requires_expiration_date = models.BooleanField(default=False, verbose_name='Requiere fecha de vencimiento')
    uses_n8n_workflow = models.BooleanField(default=False, verbose_name='Usa N8N')
    n8n_webhook_url = models.CharField(
        max_length=512,
        null=True,
        blank=True,
        validators=[URLValidator()],
        verbose_name='URL Webhook N8N'
    )
    entity_type = models.CharField(
        max_length=50,
        choices=ENTITY_TYPE_CHOICES,
        verbose_name='Tipo de entidad'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')

    class Meta:
        db_table = 'document_types'
        verbose_name = 'Tipo de Documento'
        verbose_name_plural = 'Tipos de Documentos'
        ordering = ['entity_type', 'name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['entity_type']),
            models.Index(fields=['is_mandatory']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Document(models.Model):
    """
    Documento adjunto a una entidad.

    Attributes:
        id: Identificador único UUID
        company: Empresa propietaria del documento
        entity: Entidad a la que pertenece el documento
        document_type: Tipo de documento
        file_name: Nombre del archivo
        file_size: Tamaño del archivo en bytes
        mime_type: Tipo MIME del archivo
        s3_bucket: Nombre del bucket de S3
        s3_key: Clave del archivo en S3
        s3_region: Región de S3
        issue_date: Fecha de emisión
        expiration_date: Fecha de vencimiento
        validation_status: Estado de validación (P=Pendiente, A=Aprobado, R=Rechazado)
        validation_reason: Razón de la validación
        uploaded_by: Usuario que subió el documento
        uploaded_at: Fecha de carga
        validated_at: Fecha de validación
    """
    VALIDATION_STATUS_CHOICES = ValidationStatus.CHOICES

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='Empresa'
    )
    entity = models.ForeignKey(
        Entity,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='Entidad'
    )
    document_type = models.ForeignKey(
        DocumentType,
        on_delete=models.PROTECT,
        related_name='documents',
        verbose_name='Tipo de Documento'
    )
    file_name = models.CharField(max_length=255, verbose_name='Nombre del archivo')
    file_size = models.BigIntegerField(verbose_name='Tamaño (bytes)')
    mime_type = models.CharField(max_length=100, verbose_name='Tipo MIME')
    s3_bucket = models.CharField(max_length=255, verbose_name='Bucket S3')
    s3_key = models.CharField(max_length=512, verbose_name='Clave S3')
    s3_region = models.CharField(max_length=50, verbose_name='Región S3')
    issue_date = models.DateField(null=True, blank=True, verbose_name='Fecha de emisión')
    expiration_date = models.DateField(null=True, blank=True, verbose_name='Fecha de vencimiento')
    validation_status = models.CharField(
        max_length=1,
        choices=VALIDATION_STATUS_CHOICES,
        default=ValidationStatus.PENDING,
        verbose_name='Estado de validación'
    )
    validation_reason = models.TextField(null=True, blank=True, verbose_name='Razón de validación')
    uploaded_by = models.CharField(max_length=255, verbose_name='Subido por')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de carga')
    validated_at = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de validación')

    class Meta:
        db_table = 'documents'
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['company']),
            models.Index(fields=['entity']),
            models.Index(fields=['document_type']),
            models.Index(fields=['validation_status']),
            models.Index(fields=['expiration_date']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(validation_status__in=[
                    ValidationStatus.PENDING,
                    ValidationStatus.APPROVED,
                    ValidationStatus.REJECTED
                ]),
                name='valid_validation_status'
            )
        ]

    def __str__(self):
        return f"{self.document_type.code} - {self.entity.entity_code} ({self.get_validation_status_display()})"


class DocumentValidationLog(models.Model):
    """
    Registro de auditoría de las validaciones de documentos.

    Attributes:
        id: Identificador único UUID
        document: Documento relacionado
        action: Acción realizada
        previous_status: Estado anterior
        new_status: Nuevo estado
        reason: Razón del cambio
        performed_by: Usuario que realizó la acción
        metadata: Metadatos adicionales
        created_at: Fecha de creación del registro
    """
    ACTION_CHOICES = DocumentAction.CHOICES

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='validation_logs',
        verbose_name='Documento'
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, verbose_name='Acción')
    previous_status = models.CharField(max_length=1, null=True, blank=True, verbose_name='Estado anterior')
    new_status = models.CharField(max_length=1, verbose_name='Nuevo estado')
    reason = models.TextField(null=True, blank=True, verbose_name='Razón')
    performed_by = models.CharField(max_length=255, verbose_name='Realizado por')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='Metadatos')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')

    class Meta:
        db_table = 'document_validation_logs'
        verbose_name = 'Log de Validación'
        verbose_name_plural = 'Logs de Validación'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document']),
            models.Index(fields=['action']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.get_action_display()} - {self.document.file_name} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
