"""
Factory classes for testing using factory_boy.
"""
import factory
from factory.django import DjangoModelFactory
from apps.companies.models import Company
from apps.entities.models import Entity
from apps.documents.models import DocumentType, Document, DocumentValidationLog


class CompanyFactory(DjangoModelFactory):
    class Meta:
        model = Company

    name = factory.Sequence(lambda n: f'Company {n}')
    tax_id = factory.Sequence(lambda n: f'NIT{n:010d}')
    is_active = True


class EntityFactory(DjangoModelFactory):
    class Meta:
        model = Entity

    company = factory.SubFactory(CompanyFactory)
    entity_type = 'vehicle'
    entity_code = factory.Sequence(lambda n: f'VEH{n:05d}')
    entity_name = factory.Sequence(lambda n: f'Vehicle {n}')
    metadata = {}
    is_active = True


class DocumentTypeFactory(DjangoModelFactory):
    class Meta:
        model = DocumentType

    code = factory.Sequence(lambda n: f'DOCTYPE{n}')
    name = factory.Sequence(lambda n: f'Document Type {n}')
    is_mandatory = False
    requires_issue_date = False
    requires_expiration_date = False
    uses_n8n_workflow = False
    n8n_webhook_url = None
    entity_type = 'vehicle'


class DocumentFactory(DjangoModelFactory):
    class Meta:
        model = Document

    company = factory.SubFactory(CompanyFactory)
    entity = factory.SubFactory(EntityFactory)
    document_type = factory.LazyAttribute(
        lambda obj: DocumentTypeFactory(entity_type=obj.entity.entity_type)
    )
    file_name = factory.Sequence(lambda n: f'document_{n}.pdf')
    file_size = 1024000
    mime_type = 'application/pdf'
    s3_bucket = 'failfast-docs'
    s3_key = factory.Sequence(lambda n: f'documents/doc_{n}.pdf')
    s3_region = 'us-east-1'
    validation_status = 'P'
    uploaded_by = 'test@example.com'


class DocumentValidationLogFactory(DjangoModelFactory):
    class Meta:
        model = DocumentValidationLog

    document = factory.SubFactory(DocumentFactory)
    action = 'uploaded'
    previous_status = None
    new_status = 'P'
    reason = 'Test log'
    performed_by = 'system'
    metadata = {}
