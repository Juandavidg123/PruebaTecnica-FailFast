# Arquitectura del Sistema

Documento que explica las decisiones de diseño arquitectónico del Sistema de Gestión de Documentos Empresariales de FailFast.

## Tabla de Contenidos

- [Visión General](#visión-general)
- [Arquitectura de Capas](#arquitectura-de-capas)
- [Patrones de Diseño](#patrones-de-diseño)
- [Decisiones Técnicas](#decisiones-técnicas)
- [Escalabilidad](#escalabilidad)
- [Seguridad](#seguridad)
- [Optimizaciones](#optimizaciones)

## Visión General

El sistema está diseñado como una aplicación backend modular, escalable y mantenible que sigue los principios de:

- **Separation of Concerns**: Separación clara entre capas
- **DRY (Don't Repeat Yourself)**: Reutilización de código
- **SOLID**: Principios de diseño orientado a objetos
- **API-First**: Diseño centrado en la API REST

### Stack Tecnológico

```
Cliente --> Django REST Framework API --> Service Layer --> PostgreSQL y N8n 
```

## Arquitectura de Capas

### 1. Capa de Presentación (API Layer)

**Responsabilidad**: Exponer endpoints REST y manejar requests/responses

**Componentes**:
- **ViewSets**: Lógica de endpoints
- **Serializers**: Validación y transformación de datos
- **URLs**: Ruteo de requests

### 2. Capa de Servicios (Service Layer)

**Responsabilidad**: Lógica de negocio y orquestación

**Componentes**:
- **S3Service**: Manejo de almacenamiento en AWS S3
- **N8NService**: Integración con workflows de N8N
- **DocumentValidationService**: Lógica de validación de documentos

**Decisión**: Separar la lógica de negocio de los ViewSets permite:
- Reutilización del código
- Testing más fácil
- Menor acoplamiento
- Responsabilidad única

```python
# Ejemplo de uso del Service Layer
class DocumentViewSet(viewsets.ModelViewSet):
    def upload(self, request):
        # ViewSet solo orquesta
        s3_metadata = S3Service().upload_file(...)
        document = Document.objects.create(...)
        DocumentValidationService.create_validation_log(...)
```

### 3. Capa de Datos (Data Layer)

**Responsabilidad**: Persistencia y acceso a datos

**Componentes**:
- **Models**: Definición de esquemas con validaciones personalizadas
- **Managers**: Queries personalizados para operaciones complejas
- **Migrations**: Control de versiones de BD
- **PL/pgSQL Functions**: Validaciones masivas optimizadas en base de datos

## Patrones de Diseño

### 1. Service Pattern

```python
class DocumentValidationService:
    @staticmethod
    def approve_document(document, reason, performed_by):
        # Encapsula lógica de negocio compleja
        document.validation_status = 'A'
        document.save()
        # Crear log de auditoría
        DocumentValidationService.create_validation_log(...)
```

### 2. Factory Pattern (Testing)

```python
# Uso de factory_boy para testing
class DocumentFactory(DjangoModelFactory):
    class Meta:
        model = Document
    # ...
```

### 3. Strategy Pattern (Validaciones)

```python
# Diferentes estrategias de validación según tipo de documento
if doc_type.uses_n8n_workflow:
    # Validación automática vía N8N
    N8NService().trigger_workflow(...)
else:
    # Validación manual
    DocumentValidationService.approve_document(...)
```
## Escalabilidad

### Estrategias Implementadas

#### 1. Índices de Base de Datos

```python
class Document(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['company']),
            models.Index(fields=['entity']),
            models.Index(fields=['validation_status']),
            models.Index(fields=['expiration_date']),
        ]
```

#### 2. Select Related / Prefetch Related

```python
# Evita N+1 queries
queryset = Document.objects.select_related(
    'company', 'entity', 'document_type'
).prefetch_related('validation_logs')
```

#### 3. Paginación

```python
# Configuración en settings.py
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}
```

#### 4. Almacenamiento Distribuido (S3)

- Archivos no están en el servidor de aplicación
- Escalabilidad horizontal sin compartir disco
- CDN-ready con CloudFront

### Escalabilidad Futura

**Horizontal Scaling**:
```yaml
# Docker Compose con múltiples workers
services:
  web:
    deploy:
      replicas: 3

  nginx:
    image: nginx
    # Load balancer
```

**Caché**:
```python
# Redis para caché (futuro)
from django.core.cache import cache

@cache.memoize(timeout=300)
def get_document_types(entity_type):
    return DocumentType.objects.filter(entity_type=entity_type)
```

**Procesamiento Asíncrono**:
```python
# Celery para tareas pesadas (futuro)
@celery.task
def process_bulk_validation(company_id, entity_type):
    # Validación masiva en background
```

## Seguridad

### Implementaciones Actuales

#### 1. Pre-signed URLs

```python
# URLs temporales para descarga segura
url = s3_service.generate_presigned_url(s3_key, expiration=300)
# Expira en 5 minutos
```

#### 2. Validaciones de Entrada

```python
class DocumentUploadSerializer(serializers.Serializer):
    def validate(self, data):
        # Validar tamaño de archivo
        validate_file_size(data['file'])
        # Validar tipo de archivo
        validate_file_type(data['file'])
        # Validar permisos
        if entity.company_id != data['company_id']:
            raise ValidationError(...)
```

#### 3. SQL Injection Protection

Django ORM protege automáticamente:
```python
# SEGURO - Usa prepared statements
Document.objects.filter(id=user_input)

# INSEGURO - No usar
cursor.execute(f"SELECT * FROM documents WHERE id = {user_input}")
```

### Recomendaciones Futuras

1. **Autenticación JWT**:
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}
```

2. **Permisos Granulares**:
```python
class IsCompanyOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.company.id == request.user.company_id
```

3. **Rate Limiting**:
```python
from rest_framework.throttling import AnonRateThrottle

class DocumentViewSet(viewsets.ModelViewSet):
    throttle_classes = [AnonRateThrottle]
```

## Optimizaciones

### 1. Queries Optimizados

**Problema**: N+1 queries
```python
# MAL
for document in documents:
    print(document.company.name)  # Query por cada documento
```

**Solución**: select_related
```python
# BIEN
documents = Document.objects.select_related('company')
for document in documents:
    print(document.company.name)  # No extra queries
```

### 2. Bulk Operations

```python
# Crear múltiples objetos eficientemente
Document.objects.bulk_create([doc1, doc2, doc3])

# Actualizar múltiples objetos
Document.objects.filter(company=company).update(validation_status='A')
```

### 3. Database Functions

```python
# Usar funciones de BD en vez de Python
from django.db.models import Count

Entity.objects.annotate(
    document_count=Count('documents')
).filter(document_count__lt=5)
```

### 4. Compression y Minificación

```python
# settings.py
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

## Monitoreo y Logging

### Logging Configurado

```python
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    },
}
```