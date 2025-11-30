"""
Tests for Document models.
"""
import pytest
from datetime import date, timedelta
from apps.documents.models import DocumentType, Document, DocumentValidationLog
from .factories import (
    CompanyFactory, EntityFactory, DocumentTypeFactory,
    DocumentFactory, DocumentValidationLogFactory
)


@pytest.mark.django_db
class TestCompanyModel:
    def test_create_company(self):
        """Test creating a company."""
        company = CompanyFactory(name='Test Company', tax_id='123456789')
        assert company.name == 'Test Company'
        assert company.tax_id == '123456789'
        assert company.is_active is True

    def test_company_str(self):
        """Test company string representation."""
        company = CompanyFactory(name='Test Co', tax_id='123')
        assert str(company) == 'Test Co (123)'


@pytest.mark.django_db
class TestEntityModel:
    def test_create_entity(self):
        """Test creating an entity."""
        company = CompanyFactory()
        entity = EntityFactory(
            company=company,
            entity_type='vehicle',
            entity_code='ABC123',
            entity_name='Vehicle ABC123'
        )
        assert entity.company == company
        assert entity.entity_type == 'vehicle'
        assert entity.entity_code == 'ABC123'

    def test_entity_unique_together(self):
        """Test unique constraint on company+entity_type+entity_code."""
        company = CompanyFactory()
        EntityFactory(
            company=company,
            entity_type='vehicle',
            entity_code='ABC123'
        )

        # Should raise IntegrityError for duplicate
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            EntityFactory(
                company=company,
                entity_type='vehicle',
                entity_code='ABC123'
            )


@pytest.mark.django_db
class TestDocumentTypeModel:
    def test_create_document_type(self):
        """Test creating a document type."""
        doc_type = DocumentTypeFactory(
            code='SOAT',
            name='Seguro Obligatorio',
            is_mandatory=True,
            entity_type='vehicle'
        )
        assert doc_type.code == 'SOAT'
        assert doc_type.is_mandatory is True

    def test_document_type_with_n8n(self):
        """Test document type with N8N workflow."""
        doc_type = DocumentTypeFactory(
            uses_n8n_workflow=True,
            n8n_webhook_url='http://localhost:5678/webhook/test'
        )
        assert doc_type.uses_n8n_workflow is True
        assert doc_type.n8n_webhook_url is not None


@pytest.mark.django_db
class TestDocumentModel:
    def test_create_document(self):
        """Test creating a document."""
        company = CompanyFactory()
        entity = EntityFactory(company=company)
        doc_type = DocumentTypeFactory(entity_type=entity.entity_type)

        document = DocumentFactory(
            company=company,
            entity=entity,
            document_type=doc_type,
            file_name='test.pdf'
        )

        assert document.company == company
        assert document.entity == entity
        assert document.document_type == doc_type
        assert document.validation_status == 'P'

    def test_document_with_dates(self):
        """Test document with issue and expiration dates."""
        today = date.today()
        future = today + timedelta(days=365)

        document = DocumentFactory(
            issue_date=today,
            expiration_date=future
        )

        assert document.issue_date == today
        assert document.expiration_date == future

    def test_document_validation_status_choices(self):
        """Test document validation status."""
        document = DocumentFactory(validation_status='P')
        assert document.validation_status == 'P'

        document.validation_status = 'A'
        document.save()
        assert document.validation_status == 'A'


@pytest.mark.django_db
class TestDocumentValidationLogModel:
    def test_create_validation_log(self):
        """Test creating a validation log."""
        document = DocumentFactory()
        log = DocumentValidationLogFactory(
            document=document,
            action='uploaded',
            new_status='P',
            performed_by='test@example.com'
        )

        assert log.document == document
        assert log.action == 'uploaded'
        assert log.performed_by == 'test@example.com'

    def test_log_with_metadata(self):
        """Test log with metadata."""
        log = DocumentValidationLogFactory(
            metadata={'key': 'value', 'count': 123}
        )
        assert log.metadata['key'] == 'value'
        assert log.metadata['count'] == 123
