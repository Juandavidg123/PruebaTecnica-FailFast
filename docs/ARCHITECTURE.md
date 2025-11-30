# Arquitectura

Decisiones de diseño del sistema.

## Stack

```
Cliente -> Django REST API -> Service Layer -> PostgreSQL / AWS S3 / N8N
```

## Capas

### 1. API Layer (ViewSets + Serializers)

Endpoints REST junto a Orquestación básica.

### 2. Service Layer

Lógica de negocio separada en servicios:
- `S3Service` - Manejo de AWS S3
- `N8NService` - Integración con N8N
- `DocumentValidationService` - Validaciones

Por qué: reutilización de código, testing más fácil, menor acoplamiento.

```python
class DocumentViewSet(viewsets.ModelViewSet):
    def upload(self, request):
        # Solo orquesta, no implementa lógica
        s3_metadata = S3Service().upload_file(...)
        document = Document.objects.create(...)
```

### 3. Data Layer

Modelos, managers, migraciones, funciones PL/pgSQL.

## Patrones usados

**Service Pattern** - Encapsula la lógica de negocio:
```python
class DocumentValidationService:
    @staticmethod
    def approve_document(document, reason, performed_by):
        document.validation_status = 'A'
        document.save()
        # log de auditoría...
```

**Factory Pattern** - Testing con factory_boy

**Strategy Pattern** - Diferentes validaciones según tipo:
```python
if doc_type.uses_n8n_workflow:
    N8NService().trigger_workflow(...)
else:
    DocumentValidationService.approve_document(...)
```

## Escalabilidad

**Implementado:**
- Índices en BD (company, entity, validation_status, expiration_date)
- select_related/prefetch_related para evitar N+1 queries
- Paginación (50 items por página)
- Archivos en S3 (no en servidor)

## Seguridad

**Implementado:**
- Pre-signed URLs para S3 (expiran en 5 min)
- Validaciones de entrada en serializers
- Django ORM protege contra SQL injection

## Optimizaciones

### Queries eficientes

```python
# Mal - N+1 queries
for doc in documents:
    print(doc.company.name)

# Bien - 1 query
documents = Document.objects.select_related('company')
```

### Bulk operations

```python
Document.objects.bulk_create([doc1, doc2, doc3])
Document.objects.filter(company=company).update(status='A')
```

### DB functions en vez de Python

```python
Entity.objects.annotate(
    document_count=Count('documents')
).filter(document_count__lt=5)
```

## Logging

Configurado en `settings.py` para registrar en archivo `debug.log`. Nivel INFO para Django.
