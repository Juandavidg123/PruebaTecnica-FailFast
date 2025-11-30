"""
Tests for Document services.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from django.utils import timezone
from apps.documents.services import (
    S3Service, N8NService, DocumentValidationService
)
from apps.documents.models import DocumentValidationLog
from .factories import DocumentFactory


@pytest.mark.django_db
class TestS3Service:
    @patch('apps.documents.services.boto3.client')
    def test_upload_file(self, mock_boto_client):
        """Test uploading file to S3."""
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        service = S3Service()

        # Mock file object
        mock_file = Mock()
        mock_file.name = 'test.pdf'
        mock_file.size = 1024
        mock_file.content_type = 'application/pdf'

        result = service.upload_file(
            file_obj=mock_file,
            company_id='123',
            entity_id='456',
            entity_type='vehicle',
            document_type_code='SOAT'
        )

        assert result['file_name'] == 'test.pdf'
        assert result['file_size'] == 1024
        assert result['mime_type'] == 'application/pdf'
        assert 's3_key' in result
        mock_s3.upload_fileobj.assert_called_once()

    @patch('apps.documents.services.boto3.client')
    def test_generate_presigned_url(self, mock_boto_client):
        """Test generating presigned URL."""
        mock_s3 = Mock()
        mock_s3.generate_presigned_url.return_value = 'http://example.com/file.pdf'
        mock_boto_client.return_value = mock_s3

        service = S3Service()
        url = service.generate_presigned_url('test/key.pdf', expiration=300)

        assert url == 'http://example.com/file.pdf'
        mock_s3.generate_presigned_url.assert_called_once()


@pytest.mark.django_db
class TestN8NService:
    @patch('apps.documents.services.requests.post')
    def test_trigger_workflow(self, mock_post):
        """Test triggering N8N workflow."""
        mock_response = Mock()
        mock_response.json.return_value = {'success': True}
        mock_response.content = b'{"success": true}'
        mock_post.return_value = mock_response

        service = N8NService()
        payload = {'test': 'data'}
        result = service.trigger_workflow('http://localhost:5678/webhook', payload)

        assert result == {'success': True}
        mock_post.assert_called_once()


@pytest.mark.django_db
class TestDocumentValidationService:
    def test_create_validation_log(self):
        """Test creating validation log."""
        document = DocumentFactory(validation_status='P')

        log = DocumentValidationService.create_validation_log(
            document=document,
            action='uploaded',
            new_status='P',
            performed_by='test@example.com',
            reason='Test reason'
        )

        assert isinstance(log, DocumentValidationLog)
        assert log.document == document
        assert log.action == 'uploaded'
        assert log.performed_by == 'test@example.com'

    def test_approve_document(self):
        """Test approving a document."""
        document = DocumentFactory(validation_status='P')

        updated_doc = DocumentValidationService.approve_document(
            document=document,
            reason='Document verified',
            performed_by='admin@example.com'
        )

        assert updated_doc.validation_status == 'A'
        assert updated_doc.validation_reason == 'Document verified'
        assert updated_doc.validated_at is not None

        # Check log was created
        logs = DocumentValidationLog.objects.filter(document=document, action='approved')
        assert logs.count() == 1

    def test_reject_document(self):
        """Test rejecting a document."""
        document = DocumentFactory(validation_status='P')

        updated_doc = DocumentValidationService.reject_document(
            document=document,
            reason='Invalid document',
            performed_by='admin@example.com'
        )

        assert updated_doc.validation_status == 'R'
        assert updated_doc.validation_reason == 'Invalid document'
        assert updated_doc.validated_at is not None

        # Check log was created
        logs = DocumentValidationLog.objects.filter(document=document, action='rejected')
        assert logs.count() == 1

    def test_process_n8n_callback_approved(self):
        """Test processing N8N callback for approval."""
        document = DocumentFactory(validation_status='P')

        updated_doc = DocumentValidationService.process_n8n_callback(
            document=document,
            status='approved',
            reason='OCR verified',
            metadata={'confidence': 0.98}
        )

        assert updated_doc.validation_status == 'A'
        assert updated_doc.validation_reason == 'OCR verified'

        # Check log
        logs = DocumentValidationLog.objects.filter(
            document=document,
            action='n8n_callback'
        )
        assert logs.count() == 1
        assert logs.first().metadata['confidence'] == 0.98

    def test_process_n8n_callback_rejected(self):
        """Test processing N8N callback for rejection."""
        document = DocumentFactory(validation_status='P')

        updated_doc = DocumentValidationService.process_n8n_callback(
            document=document,
            status='rejected',
            reason='Failed OCR validation',
            metadata={'error': 'low confidence'}
        )

        assert updated_doc.validation_status == 'R'
        assert updated_doc.validation_reason == 'Failed OCR validation'
