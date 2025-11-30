"""
Django signals for Document Management System.
Implements the Observer pattern for document events.
"""
from django.dispatch import Signal, receiver
from django.utils import timezone
from .models import Document, DocumentValidationLog
from .constants import DocumentAction, ValidationStatus

# Define custom signals
document_uploaded = Signal()
document_approved = Signal()
document_rejected = Signal()
document_n8n_sent = Signal()
document_n8n_callback_received = Signal()


@receiver(document_uploaded)
def log_document_upload(sender, document, performed_by, reason, **kwargs):
    """Log when a document is uploaded."""
    DocumentValidationLog.objects.create(
        document=document,
        action=DocumentAction.UPLOADED,
        previous_status=None,
        new_status=ValidationStatus.PENDING,
        reason=reason,
        performed_by=performed_by,
        metadata=kwargs.get('metadata', {})
    )


@receiver(document_approved)
def log_document_approval(sender, document, performed_by, reason, **kwargs):
    """Log when a document is approved."""
    previous_status = document.validation_status

    DocumentValidationLog.objects.create(
        document=document,
        action=DocumentAction.APPROVED,
        previous_status=previous_status,
        new_status=ValidationStatus.APPROVED,
        reason=reason,
        performed_by=performed_by,
        metadata=kwargs.get('metadata', {})
    )


@receiver(document_rejected)
def log_document_rejection(sender, document, performed_by, reason, **kwargs):
    """Log when a document is rejected."""
    previous_status = document.validation_status

    DocumentValidationLog.objects.create(
        document=document,
        action=DocumentAction.REJECTED,
        previous_status=previous_status,
        new_status=ValidationStatus.REJECTED,
        reason=reason,
        performed_by=performed_by,
        metadata=kwargs.get('metadata', {})
    )


@receiver(document_n8n_sent)
def log_n8n_sent(sender, document, webhook_url, **kwargs):
    """Log when a document is sent to N8N."""
    DocumentValidationLog.objects.create(
        document=document,
        action=DocumentAction.N8N_SENT,
        previous_status=document.validation_status,
        new_status=ValidationStatus.PENDING,
        reason='Documento enviado a N8N para validación',
        performed_by='system',
        metadata={'webhook_url': webhook_url}
    )


@receiver(document_n8n_sent)
def handle_n8n_send_failure(sender, document, error, **kwargs):
    """Log when N8N send fails."""
    if error:
        DocumentValidationLog.objects.create(
            document=document,
            action=DocumentAction.N8N_SENT,
            previous_status=document.validation_status,
            new_status=ValidationStatus.PENDING,
            reason=f'Error al enviar a N8N: {str(error)}',
            performed_by='system',
            metadata={'error': str(error)}
        )


@receiver(document_n8n_callback_received)
def log_n8n_callback(sender, document, status, reason, metadata, **kwargs):
    """Log when N8N callback is received."""
    previous_status = document.validation_status
    new_status = ValidationStatus.APPROVED if status == 'approved' else ValidationStatus.REJECTED

    DocumentValidationLog.objects.create(
        document=document,
        action=DocumentAction.N8N_CALLBACK,
        previous_status=previous_status,
        new_status=new_status,
        reason=reason,
        performed_by='n8n',
        metadata=metadata or {}
    )


# Future: Add more signal handlers as needed
# Example:
# @receiver(document_approved)
# def send_approval_notification(sender, document, **kwargs):
#     """Send notification when document is approved."""
#     # Send email, webhook, etc.
#     pass
