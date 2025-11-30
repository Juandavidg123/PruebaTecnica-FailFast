"""
Service layer for document management.
Handles S3 uploads, N8N webhooks, and business logic.
"""
import boto3
import requests
import mimetypes
from datetime import datetime
from typing import Dict, Any, Optional
from django.conf import settings
from django.utils import timezone
from botocore.exceptions import ClientError
from .models import Document
from .constants import ValidationStatus, DocumentAction, N8NStatus
from .signals import (
    document_uploaded, document_approved, document_rejected,
    document_n8n_sent, document_n8n_callback_received
)
from .repositories import DocumentRepository, DocumentValidationLogRepository


class S3Service:
    """
    Service for interacting with AWS S3.
    """

    def __init__(self):
        from botocore.config import Config

        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
            config=Config(signature_version='s3v4')
        )
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        self.region = settings.AWS_S3_REGION_NAME

    def upload_file(self, file_obj, company_id: str, entity_id: str,
                   entity_type: str, document_type_code: str) -> Dict[str, str]:
        """
        Sube un archivo a S3 y retorna los metadatos.

        Args:
            file_obj: Objeto de archivo de Django
            company_id: ID de la empresa
            entity_id: ID de la entidad
            entity_type: Tipo de entidad (vehicle, employee, etc.)
            document_type_code: Código del tipo de documento

        Returns:
            Dict con bucket, key, region, file_name, file_size, mime_type
        """
        # Generar la clave S3
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_extension = file_obj.name.split('.')[-1] if '.' in file_obj.name else ''
        s3_key = (
            f"companies/{company_id}/"
            f"{entity_type}s/{entity_id}/"
            f"{document_type_code}_{timestamp}.{file_extension}"
        )

        # Determinar tipo MIME
        mime_type = file_obj.content_type if hasattr(file_obj, 'content_type') else None
        if not mime_type:
            mime_type = mimetypes.guess_type(file_obj.name)[0] or 'application/octet-stream'

        try:
            # Subir a S3
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': mime_type,
                    'Metadata': {
                        'company_id': str(company_id),
                        'entity_id': str(entity_id),
                        'entity_type': entity_type,
                        'document_type': document_type_code
                    }
                }
            )

            return {
                's3_bucket': self.bucket_name,
                's3_key': s3_key,
                's3_region': self.region,
                'file_name': file_obj.name,
                'file_size': file_obj.size,
                'mime_type': mime_type
            }

        except ClientError as e:
            raise Exception(f"Error al subir archivo a S3: {str(e)}")

    def generate_presigned_url(self, s3_key: str, expiration: int = 300) -> str:
        """
        Genera una URL pre-firmada para descargar un archivo de S3.

        Args:
            s3_key: Clave del archivo en S3
            expiration: Tiempo de expiración en segundos (default: 5 minutos)

        Returns:
            URL pre-firmada
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            raise Exception(f"Error al generar URL pre-firmada: {str(e)}")

    def delete_file(self, s3_key: str) -> bool:
        """
        Elimina un archivo de S3.

        Args:
            s3_key: Clave del archivo en S3

        Returns:
            True si se eliminó correctamente
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except ClientError as e:
            raise Exception(f"Error al eliminar archivo de S3: {str(e)}")


class N8NService:
    """
    Service for interacting with N8N workflows.
    """

    def __init__(self):
        self.base_url = settings.N8N_BASE_URL
        self.api_key = settings.N8N_API_KEY

    def trigger_workflow(self, webhook_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispara un workflow de N8N mediante webhook.

        Args:
            webhook_url: URL del webhook de N8N
            payload: Datos a enviar

        Returns:
            Respuesta del webhook
        """
        try:
            headers = {
                'Content-Type': 'application/json',
            }

            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'

            response = requests.post(
                webhook_url,
                json=payload,
                headers=headers,
                timeout=30
            )

            response.raise_for_status()
            return response.json() if response.content else {}

        except requests.exceptions.RequestException as e:
            raise Exception(f"Error al disparar webhook N8N: {str(e)}")


class DocumentValidationService:
    """
    Service for document validation business logic.
    Uses signals for event-driven architecture.
    """

    @staticmethod
    def approve_document(document: Document, reason: str, performed_by: str) -> Document:
        """
        Aprueba un documento.

        Args:
            document: Documento a aprobar
            reason: Razón de la aprobación
            performed_by: Usuario que aprueba

        Returns:
            Documento actualizado
        """
        document.validation_status = ValidationStatus.APPROVED
        document.validation_reason = reason
        document.validated_at = timezone.now()
        document.save()

        # Emit signal - observers will handle logging and other side effects
        document_approved.send(
            sender=DocumentValidationService,
            document=document,
            performed_by=performed_by,
            reason=reason
        )

        return document

    @staticmethod
    def reject_document(document: Document, reason: str, performed_by: str) -> Document:
        """
        Rechaza un documento.

        Args:
            document: Documento a rechazar
            reason: Razón del rechazo
            performed_by: Usuario que rechaza

        Returns:
            Documento actualizado
        """
        document.validation_status = ValidationStatus.REJECTED
        document.validation_reason = reason
        document.validated_at = timezone.now()
        document.save()

        # Emit signal - observers will handle logging and other side effects
        document_rejected.send(
            sender=DocumentValidationService,
            document=document,
            performed_by=performed_by,
            reason=reason
        )

        return document

    @staticmethod
    def process_n8n_callback(document: Document, status: str, reason: str,
                            metadata: Optional[Dict] = None) -> Document:
        """
        Procesa el callback de N8N.

        Args:
            document: Documento
            status: Estado retornado por N8N ('approved' o 'rejected')
            reason: Razón de la decisión
            metadata: Metadatos adicionales de N8N

        Returns:
            Documento actualizado
        """
        if status == N8NStatus.APPROVED:
            new_status = ValidationStatus.APPROVED
        else:
            new_status = ValidationStatus.REJECTED

        document.validation_status = new_status
        document.validation_reason = reason
        document.validated_at = timezone.now()
        document.save()

        # Emit signal - observers will handle logging and other side effects
        document_n8n_callback_received.send(
            sender=DocumentValidationService,
            document=document,
            status=status,
            reason=reason,
            metadata=metadata or {}
        )

        return document
