"""
API tests for Document endpoints.
"""
import pytest
from io import BytesIO
from datetime import date, timedelta
from unittest.mock import patch, Mock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.documents.models import Document, DocumentValidationLog
from .factories import (
    CompanyFactory, EntityFactory, DocumentTypeFactory,
    DocumentFactory
)


@pytest.fixture
def api_client():
    """Return API client."""
    return APIClient()


@pytest.mark.django_db
class TestDocumentTypeAPI:
    def test_list_document_types(self, api_client):
        """Test listing document types."""
        DocumentTypeFactory.create_batch(3)

        url = reverse('document-type-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3

    def test_create_document_type(self, api_client):
        """Test creating document type."""
        url = reverse('document-type-list')
        data = {
            'code': 'SOAT',
            'name': 'Seguro Obligatorio',
            'is_mandatory': True,
            'entity_type': 'vehicle'
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['code'] == 'SOAT'


@pytest.mark.django_db
class TestDocumentAPI:
    def test_list_documents(self, api_client):
        """Test listing documents."""
        DocumentFactory.create_batch(5)

        url = reverse('document-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 5

    @patch('apps.documents.views.S3Service')
    def test_upload_document(self, mock_s3_service, api_client):
        """Test uploading a document."""
        # Setup mocks
        mock_s3 = Mock()
        mock_s3.upload_file.return_value = {
            's3_bucket': 'test-bucket',
            's3_key': 'test/key.pdf',
            's3_region': 'us-east-1',
            'file_name': 'test.pdf',
            'file_size': 1024,
            'mime_type': 'application/pdf'
        }
        mock_s3_service.return_value = mock_s3

        # Create test data
        company = CompanyFactory()
        entity = EntityFactory(company=company, entity_type='vehicle')
        doc_type = DocumentTypeFactory(
            entity_type='vehicle',
            uses_n8n_workflow=False
        )

        # Create file
        file_content = b'PDF content here'
        test_file = BytesIO(file_content)
        test_file.name = 'test.pdf'

        url = reverse('document-upload')
        data = {
            'company_id': str(company.id),
            'entity_id': str(entity.id),
            'document_type_id': str(doc_type.id),
            'file': test_file,
            'uploaded_by': 'test@example.com'
        }

        response = api_client.post(url, data, format='multipart')

        assert response.status_code == status.HTTP_201_CREATED
        assert 'id' in response.data
        assert response.data['status'] == 'P'

    def test_approve_document(self, api_client):
        """Test approving a document."""
        doc_type = DocumentTypeFactory(uses_n8n_workflow=False)
        document = DocumentFactory(
            document_type=doc_type,
            validation_status='P'
        )

        url = reverse('document-approve', kwargs={'pk': document.id})
        data = {
            'reason': 'Document verified manually',
            'performed_by': 'admin@example.com'
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        document.refresh_from_db()
        assert document.validation_status == 'A'

    def test_reject_document(self, api_client):
        """Test rejecting a document."""
        document = DocumentFactory(validation_status='P')

        url = reverse('document-reject', kwargs={'pk': document.id})
        data = {
            'reason': 'Invalid date',
            'performed_by': 'admin@example.com'
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        document.refresh_from_db()
        assert document.validation_status == 'R'

    @patch('apps.documents.views.S3Service')
    def test_download_document(self, mock_s3_service, api_client):
        """Test downloading a document."""
        mock_s3 = Mock()
        mock_s3.generate_presigned_url.return_value = 'http://example.com/download'
        mock_s3_service.return_value = mock_s3

        document = DocumentFactory()

        url = reverse('document-download', kwargs={'pk': document.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'download_url' in response.data
        assert response.data['download_url'] == 'http://example.com/download'

    def test_n8n_callback_approved(self, api_client):
        """Test N8N callback for approval."""
        document = DocumentFactory(validation_status='P')

        url = reverse('document-n8n-callback', kwargs={'pk': document.id})
        data = {
            'status': 'approved',
            'reason': 'OCR verified',
            'metadata': {'confidence': 0.98}
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        document.refresh_from_db()
        assert document.validation_status == 'A'

    def test_n8n_callback_rejected(self, api_client):
        """Test N8N callback for rejection."""
        document = DocumentFactory(validation_status='P')

        url = reverse('document-n8n-callback', kwargs={'pk': document.id})
        data = {
            'status': 'rejected',
            'reason': 'Failed OCR',
            'metadata': {}
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        document.refresh_from_db()
        assert document.validation_status == 'R'

    def test_n8n_callback_already_processed(self, api_client):
        """Test N8N callback on already processed document."""
        document = DocumentFactory(validation_status='A')

        url = reverse('document-n8n-callback', kwargs={'pk': document.id})
        data = {
            'status': 'approved',
            'reason': 'Test',
            'metadata': {}
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
