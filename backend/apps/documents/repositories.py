"""
Repository pattern implementation for Document Management System.
Provides abstraction layer between business logic and data access.
"""
from typing import Optional, List
from uuid import UUID
from django.db.models import QuerySet
from .models import Document, DocumentType, DocumentValidationLog
from .constants import ValidationStatus


class DocumentRepository:
    """Repository for Document data access operations."""

    @staticmethod
    def find_by_id(document_id: UUID) -> Optional[Document]:
        """Find a document by its ID."""
        try:
            return Document.objects.select_related(
                'company', 'entity', 'document_type'
            ).get(id=document_id)
        except Document.DoesNotExist:
            return None

    @staticmethod
    def find_by_entity_and_type(entity_id: UUID, doc_type_id: UUID) -> Optional[Document]:
        """Find a document by entity and document type."""
        return Document.objects.filter(
            entity_id=entity_id,
            document_type_id=doc_type_id
        ).first()

    @staticmethod
    def find_pending_documents(company_id: UUID) -> QuerySet:
        """Find all pending documents for a company."""
        return Document.objects.filter(
            company_id=company_id,
            validation_status=ValidationStatus.PENDING
        ).select_related('company', 'entity', 'document_type')

    @staticmethod
    def find_by_status(company_id: UUID, status: str) -> QuerySet:
        """Find documents by company and validation status."""
        return Document.objects.filter(
            company_id=company_id,
            validation_status=status
        ).select_related('company', 'entity', 'document_type')

    @staticmethod
    def find_expired_documents(company_id: UUID) -> QuerySet:
        """Find all expired approved documents for a company."""
        from django.utils import timezone
        return Document.objects.filter(
            company_id=company_id,
            validation_status=ValidationStatus.APPROVED,
            expiration_date__lt=timezone.now().date()
        ).select_related('company', 'entity', 'document_type')

    @staticmethod
    def create(document_data: dict) -> Document:
        """Create a new document."""
        return Document.objects.create(**document_data)

    @staticmethod
    def update(document: Document, **kwargs) -> Document:
        """Update a document with the provided fields."""
        for key, value in kwargs.items():
            setattr(document, key, value)
        document.save()
        return document


class DocumentTypeRepository:
    """Repository for DocumentType data access operations."""

    @staticmethod
    def find_by_id(doc_type_id: UUID) -> Optional[DocumentType]:
        """Find a document type by its ID."""
        try:
            return DocumentType.objects.get(id=doc_type_id)
        except DocumentType.DoesNotExist:
            return None

    @staticmethod
    def find_by_code(code: str) -> Optional[DocumentType]:
        """Find a document type by its code."""
        try:
            return DocumentType.objects.get(code=code)
        except DocumentType.DoesNotExist:
            return None

    @staticmethod
    def find_mandatory_by_entity_type(entity_type: str) -> QuerySet:
        """Find all mandatory document types for an entity type."""
        return DocumentType.objects.filter(
            entity_type=entity_type,
            is_mandatory=True
        )

    @staticmethod
    def find_by_entity_type(entity_type: str) -> QuerySet:
        """Find all document types for an entity type."""
        return DocumentType.objects.filter(entity_type=entity_type)


class DocumentValidationLogRepository:
    """Repository for DocumentValidationLog data access operations."""

    @staticmethod
    def create(log_data: dict) -> DocumentValidationLog:
        """Create a new validation log entry."""
        return DocumentValidationLog.objects.create(**log_data)

    @staticmethod
    def find_by_document(document_id: UUID) -> QuerySet:
        """Find all validation logs for a document."""
        return DocumentValidationLog.objects.filter(
            document_id=document_id
        ).order_by('-created_at')

    @staticmethod
    def find_by_action(document_id: UUID, action: str) -> QuerySet:
        """Find validation logs for a document filtered by action."""
        return DocumentValidationLog.objects.filter(
            document_id=document_id,
            action=action
        ).order_by('-created_at')
