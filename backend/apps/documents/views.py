"""
Views for Document Management System.
"""
from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import DocumentType, Document, DocumentValidationLog
from .serializers import (
    DocumentTypeSerializer, DocumentSerializer, DocumentValidationLogSerializer,
    DocumentUploadSerializer, DocumentApproveRejectSerializer,
    N8NCallbackSerializer, DocumentValidateSerializer
)
from .services import S3Service, N8NService, DocumentValidationService
from .constants import ValidationStatus, DocumentAction
from .signals import document_uploaded, document_n8n_sent


class DocumentTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar tipos de documentos.

    list: Listar todos los tipos de documentos
    create: Crear un nuevo tipo de documento
    retrieve: Obtener detalle de un tipo de documento
    update: Actualizar un tipo de documento
    partial_update: Actualizar parcialmente un tipo de documento
    destroy: Eliminar un tipo de documento
    """
    queryset = DocumentType.objects.all()
    serializer_class = DocumentTypeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['entity_type', 'is_mandatory', 'uses_n8n_workflow']
    search_fields = ['code', 'name']
    ordering_fields = ['code', 'name', 'created_at']
    ordering = ['entity_type', 'name']


class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar documentos.

    list: Listar todos los documentos
    retrieve: Obtener detalle de un documento
    """
    queryset = Document.objects.select_related(
        'company', 'entity', 'document_type'
    ).prefetch_related('validation_logs').all()
    serializer_class = DocumentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['company', 'entity', 'document_type', 'validation_status']
    search_fields = ['file_name', 'entity__entity_code', 'entity__entity_name']
    ordering_fields = ['uploaded_at', 'expiration_date', 'file_name']
    ordering = ['-uploaded_at']

    # Serializer class mapping - follows Open/Closed Principle
    serializer_classes = {
        'upload': DocumentUploadSerializer,
        'approve': DocumentApproveRejectSerializer,
        'reject': DocumentApproveRejectSerializer,
        'n8n_callback': N8NCallbackSerializer,
        'validate': DocumentValidateSerializer,
    }

    def __init__(self, *args, s3_service=None, n8n_service=None, **kwargs):
        """
        Initialize with dependency injection support.

        Args:
            s3_service: S3Service instance (injected for testing)
            n8n_service: N8NService instance (injected for testing)
        """
        super().__init__(*args, **kwargs)
        self.s3_service = s3_service or S3Service()
        self.n8n_service = n8n_service or N8NService()

    def get_serializer_class(self):
        """Return appropriate serializer based on action using dictionary mapping."""
        return self.serializer_classes.get(self.action, DocumentSerializer)

    def _upload_file_to_s3(self, file_obj, company, entity, doc_type):
        """Upload file to S3 and return metadata."""
        return self.s3_service.upload_file(
            file_obj=file_obj,
            company_id=str(company.id),
            entity_id=str(entity.id),
            entity_type=entity.entity_type,
            document_type_code=doc_type.code
        )

    def _create_document(self, company, entity, doc_type, s3_metadata, validated_data):
        """Create document record in database."""
        return Document.objects.create(
            company=company,
            entity=entity,
            document_type=doc_type,
            file_name=s3_metadata['file_name'],
            file_size=s3_metadata['file_size'],
            mime_type=s3_metadata['mime_type'],
            s3_bucket=s3_metadata['s3_bucket'],
            s3_key=s3_metadata['s3_key'],
            s3_region=s3_metadata['s3_region'],
            issue_date=validated_data.get('issue_date'),
            expiration_date=validated_data.get('expiration_date'),
            validation_status=ValidationStatus.PENDING,
            uploaded_by=validated_data.get('uploaded_by', 'system')
        )

    def _build_n8n_payload(self, document, company, entity, doc_type, callback_url):
        """Build payload for N8N webhook."""
        s3_url = self.s3_service.generate_presigned_url(
            s3_key=document.s3_key,
            expiration=3600  # 1 hora
        )

        return {
            'document_id': str(document.id),
            'company_id': str(company.id),
            'entity_type': entity.entity_type,
            'entity_id': str(entity.id),
            'entity_code': entity.entity_code,
            'document_type': doc_type.code,
            'file_name': document.file_name,
            's3_bucket': document.s3_bucket,
            's3_key': document.s3_key,
            's3_url': s3_url,
            'issue_date': str(document.issue_date) if document.issue_date else None,
            'expiration_date': str(document.expiration_date) if document.expiration_date else None,
            'callback_url': callback_url
        }

    def _trigger_n8n_workflow(self, document, company, entity, doc_type):
        """Trigger N8N workflow if needed and return success status."""
        if not (doc_type.uses_n8n_workflow and doc_type.n8n_webhook_url):
            return False

        try:
            callback_base = settings.DJANGO_CALLBACK_BASE_URL
            callback_url = f"{callback_base}/api/documents/{document.id}/n8n-callback/"

            payload = self._build_n8n_payload(document, company, entity, doc_type, callback_url)
            self.n8n_service.trigger_workflow(doc_type.n8n_webhook_url, payload)

            # Emit signal for successful N8N send
            document_n8n_sent.send(
                sender=self.__class__,
                document=document,
                webhook_url=doc_type.n8n_webhook_url,
                error=None
            )
            return True

        except Exception as e:
            # Emit signal for failed N8N send
            document_n8n_sent.send(
                sender=self.__class__,
                document=document,
                webhook_url=doc_type.n8n_webhook_url,
                error=e
            )
            return False

    def _build_upload_response(self, document, n8n_triggered):
        """Build response for upload endpoint."""
        return {
            'id': str(document.id),
            'status': document.validation_status,
            'message': 'Documento cargado exitosamente',
            'n8n_triggered': n8n_triggered
        }

    @swagger_auto_schema(
        method='post',
        request_body=DocumentUploadSerializer,
        responses={
            201: openapi.Response(
                description="Documento cargado exitosamente",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_STRING, format='uuid'),
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'n8n_triggered': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    }
                )
            )
        }
    )
    @action(detail=False, methods=['post'])
    def upload(self, request):
        """
        Cargar un nuevo documento.

        Este endpoint:
        1. Valida los datos del documento
        2. Sube el archivo a S3
        3. Crea el registro en la base de datos
        4. Si el tipo de documento usa N8N, dispara el webhook
        5. Registra la acción en el log de auditoría
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        company = validated_data['_company']
        entity = validated_data['_entity']
        doc_type = validated_data['_document_type']
        file_obj = validated_data['file']

        try:
            with transaction.atomic():
                # Upload file to S3
                s3_metadata = self._upload_file_to_s3(file_obj, company, entity, doc_type)

                # Create document in database
                document = self._create_document(company, entity, doc_type, s3_metadata, validated_data)

                # Emit signal for document upload
                document_uploaded.send(
                    sender=self.__class__,
                    document=document,
                    performed_by=document.uploaded_by,
                    reason='Documento cargado exitosamente'
                )

            # Trigger N8N workflow if needed (outside transaction)
            n8n_triggered = self._trigger_n8n_workflow(document, company, entity, doc_type)

            return Response(
                self._build_upload_response(document, n8n_triggered),
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            # Clean up S3 file if it was uploaded but DB transaction failed
            if 's3_metadata' in locals():
                try:
                    self.s3_service.delete_file(s3_metadata['s3_key'])
                except Exception:
                    pass  # Log this in production

            return Response({
                'error': True,
                'message': f'Error al cargar documento: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        method='get',
        responses={
            200: openapi.Response(
                description="URL de descarga generada",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'document_id': openapi.Schema(type=openapi.TYPE_STRING, format='uuid'),
                        'file_name': openapi.Schema(type=openapi.TYPE_STRING),
                        'download_url': openapi.Schema(type=openapi.TYPE_STRING),
                        'expires_in': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                )
            )
        }
    )
    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        """
        Obtener URL pre-firmada para descargar un documento.
        """
        document = self.get_object()

        try:
            download_url = self.s3_service.generate_presigned_url(
                s3_key=document.s3_key,
                expiration=300  # 5 minutos
            )

            return Response({
                'document_id': str(document.id),
                'file_name': document.file_name,
                'download_url': download_url,
                'expires_in': 300
            })

        except Exception as e:
            return Response({
                'error': True,
                'message': f'Error al generar URL de descarga: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        method='post',
        request_body=DocumentApproveRejectSerializer,
        responses={200: DocumentSerializer()}
    )
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Aprobar un documento manualmente (sin N8N).
        """
        document = self.get_object()

        # Validar que el documento no use N8N
        if document.document_type.uses_n8n_workflow:
            return Response({
                'error': True,
                'message': 'Este tipo de documento requiere validación mediante N8N'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            DocumentValidationService.approve_document(
                document=document,
                reason=serializer.validated_data['reason'],
                performed_by=serializer.validated_data.get('performed_by', 'system')
            )

            return Response(DocumentSerializer(document).data)

        except Exception as e:
            return Response({
                'error': True,
                'message': f'Error al aprobar documento: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        method='post',
        request_body=DocumentApproveRejectSerializer,
        responses={200: DocumentSerializer()}
    )
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Rechazar un documento.
        """
        document = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            DocumentValidationService.reject_document(
                document=document,
                reason=serializer.validated_data['reason'],
                performed_by=serializer.validated_data.get('performed_by', 'system')
            )

            return Response(DocumentSerializer(document).data)

        except Exception as e:
            return Response({
                'error': True,
                'message': f'Error al rechazar documento: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        method='post',
        request_body=N8NCallbackSerializer,
        responses={200: DocumentSerializer()}
    )
    @action(detail=True, methods=['post'], url_path='n8n-callback')
    def n8n_callback(self, request, pk=None):
        """
        Recibir respuesta de N8N sobre la validación del documento.
        """
        document = self.get_object()

        # Validar que el documento esté en estado pendiente
        if document.validation_status != ValidationStatus.PENDING:
            return Response({
                'error': True,
                'message': f'El documento ya fue procesado. Estado actual: {document.get_validation_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            DocumentValidationService.process_n8n_callback(
                document=document,
                status=serializer.validated_data['status'],
                reason=serializer.validated_data['reason'],
                metadata=serializer.validated_data.get('metadata', {})
            )

            return Response(DocumentSerializer(document).data)

        except Exception as e:
            return Response({
                'error': True,
                'message': f'Error al procesar callback de N8N: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        method='post',
        request_body=DocumentValidateSerializer,
        responses={
            200: openapi.Response(
                description="Validación masiva completada",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'validated_entities': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'total_errors': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'errors': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'entity_id': openapi.Schema(type=openapi.TYPE_STRING),
                                    'entity_code': openapi.Schema(type=openapi.TYPE_STRING),
                                    'document_type': openapi.Schema(type=openapi.TYPE_STRING),
                                    'error_type': openapi.Schema(type=openapi.TYPE_STRING),
                                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                                }
                            )
                        ),
                    }
                )
            )
        }
    )
    @action(detail=False, methods=['post'])
    def validate(self, request):
        """
        Validación masiva de documentos usando PL/pgSQL.

        Esta función ejecuta validaciones a nivel de base de datos:
        - Documentos obligatorios faltantes
        - Documentos con fechas de emisión futuras
        - Documentos vencidos
        - Documentos rechazados activos
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        company_id = serializer.validated_data['company_id']
        entity_type = serializer.validated_data['entity_type']
        entity_ids = serializer.validated_data.get('entity_ids')

        try:
            with connection.cursor() as cursor:
                # Llamar a la función PL/pgSQL
                if entity_ids:
                    cursor.execute("""
                        SELECT * FROM fn_validate_documents_bulk(
                            %s::uuid,
                            %s::varchar,
                            %s::uuid[]
                        )
                    """, [str(company_id), entity_type, [str(eid) for eid in entity_ids]])
                else:
                    cursor.execute("""
                        SELECT * FROM fn_validate_documents_bulk(
                            %s::uuid,
                            %s::varchar,
                            NULL
                        )
                    """, [str(company_id), entity_type])

                # Obtener resultados
                columns = [col[0] for col in cursor.description]
                errors = [
                    dict(zip(columns, row))
                    for row in cursor.fetchall()
                ]

            # Contar entidades validadas
            validated_entities = len(set(error['entity_id'] for error in errors)) if errors else 0

            return Response({
                'validated_entities': validated_entities,
                'total_errors': len(errors),
                'errors': errors
            })

        except Exception as e:
            return Response({
                'error': True,
                'message': f'Error en validación masiva: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentValidationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar logs de validación (solo lectura).

    list: Listar todos los logs
    retrieve: Obtener detalle de un log
    """
    queryset = DocumentValidationLog.objects.select_related('document').all()
    serializer_class = DocumentValidationLogSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['document', 'action', 'performed_by']
    search_fields = ['reason', 'performed_by']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
