# API Documentation

Base URL: `http://localhost:8000/api/`

## Companies

### Listar
```http
GET /api/companies/
```
Query params: `is_active`, `search`, `ordering`

### Crear
```http
POST /api/companies/
```
```json
{
  "name": "Mi Empresa",
  "tax_id": "900123456-7",
  "is_active": true
}
```

### Ver / Actualizar / Eliminar
```http
GET /api/companies/{id}/
PUT /api/companies/{id}/
PATCH /api/companies/{id}/
DELETE /api/companies/{id}/
```

## Entities

### Listar
```http
GET /api/entities/
```
Query params: `company`, `entity_type`, `is_active`, `search`

### Crear
```http
POST /api/entities/
```
```json
{
  "company": "uuid",
  "entity_type": "vehicle",
  "entity_code": "ABC123",
  "entity_name": "Vehículo ABC123",
  "metadata": {
    "brand": "Toyota",
    "model": "Hilux",
    "year": 2023
  }
}
```

Tipos disponibles: `vehicle`, `employee`, `supplier`, `asset`

## Document Types

### Listar
```http
GET /api/document-types/
```
Query params: `entity_type`, `is_mandatory`, `uses_n8n_workflow`

### Crear
```http
POST /api/document-types/
```
```json
{
  "code": "SOAT",
  "name": "Seguro Obligatorio",
  "is_mandatory": true,
  "requires_issue_date": true,
  "requires_expiration_date": true,
  "uses_n8n_workflow": false,
  "entity_type": "vehicle"
}
```

Con N8N:
```json
{
  "code": "LICENCIA",
  "name": "Licencia de Conducción",
  "is_mandatory": true,
  "uses_n8n_workflow": true,
  "n8n_webhook_url": "http://localhost:5678/webhook/validate",
  "entity_type": "employee"
}
```

## Documents

### Listar
```http
GET /api/documents/
```
Query params: `company`, `entity`, `document_type`, `validation_status` (P/A/R)

### Upload
```http
POST /api/documents/upload/
```
Multipart form-data:
- `company_id` (uuid)
- `entity_id` (uuid)
- `document_type_id` (uuid)
- `file` (archivo)
- `issue_date` (YYYY-MM-DD, opcional)
- `expiration_date` (YYYY-MM-DD, opcional)
- `uploaded_by` (email, opcional)

Ejemplo:
```bash
curl -X POST http://localhost:8000/api/documents/upload/ \
  -F "company_id=uuid" \
  -F "entity_id=uuid" \
  -F "document_type_id=uuid" \
  -F "file=@soat.pdf" \
  -F "issue_date=2024-01-15" \
  -F "expiration_date=2025-01-15"
```

Response:
```json
{
  "id": "uuid",
  "status": "P",
  "message": "Documento cargado exitosamente",
  "n8n_triggered": false
}
```

### Download
```http
GET /api/documents/{id}/download/
```
Retorna pre-signed URL válida por 5 minutos.

### Aprobar
```http
POST /api/documents/{id}/approve/
```
```json
{
  "reason": "Verificado manualmente",
  "performed_by": "admin@ejemplo.com"
}
```
Solo para documentos sin N8N workflow.

### Rechazar
```http
POST /api/documents/{id}/reject/
```
```json
{
  "reason": "Fecha incorrecta",
  "performed_by": "admin@ejemplo.com"
}
```

### N8N Callback
```http
POST /api/documents/{id}/n8n-callback/
```
Aprobado:
```json
{
  "status": "approved",
  "reason": "OCR validado",
  "metadata": {"ocr_confidence": 0.98}
}
```

Rechazado:
```json
{
  "status": "rejected",
  "reason": "OCR no pudo leer",
  "metadata": {"error": "low_confidence"}
}
```

### Validación Masiva
```http
POST /api/documents/validate/
```

Todas las entidades:
```json
{
  "company_id": "uuid",
  "entity_type": "vehicle",
  "entity_ids": null
}
```

Entidades específicas:
```json
{
  "company_id": "uuid",
  "entity_type": "vehicle",
  "entity_ids": ["uuid1", "uuid2"]
}
```

Response:
```json
{
  "validated_entities": 3,
  "total_errors": 5,
  "errors": [
    {
      "entity_id": "uuid",
      "entity_code": "ABC123",
      "document_type_code": "SOAT",
      "error_type": "missing_mandatory",
      "error_message": "Documento obligatorio faltante: SOAT"
    },
    {
      "entity_id": "uuid",
      "entity_code": "ABC123",
      "document_type_code": "TECNICOMECANICA",
      "error_type": "expired",
      "error_message": "Documento vencido desde 2024-10-01"
    }
  ]
}
```

Tipos de error: `missing_mandatory`, `future_issue_date`, `expired`, `rejected`

## Validation Logs

### Listar
```http
GET /api/validation-logs/
```
Query params: `document`, `action`, `performed_by`

Response:
```json
{
  "count": 20,
  "results": [
    {
      "id": "uuid",
      "document": "uuid",
      "action": "uploaded",
      "previous_status": null,
      "new_status": "P",
      "reason": "Documento cargado",
      "performed_by": "user@example.com",
      "created_at": "2024-01-15T11:00:00Z"
    }
  ]
}
```

### Ver
```http
GET /api/validation-logs/{id}/
```

## Errores

Formato estándar:
```json
{
  "error": true,
  "message": "Descripción",
  "details": {
    "field": ["error específico"]
  }
}
```

Ejemplos:

Validación:
```json
{
  "error": true,
  "message": "Invalid input.",
  "details": {
    "tax_id": ["Este campo no puede estar vacío."]
  }
}
```

Not found:
```json
{
  "error": true,
  "message": "Not found.",
  "details": {"detail": "No encontrado."}
}
```

---

**Documentación Extra:**
- Swagger UI: http://localhost:8000/swagger/
- ReDoc: http://localhost:8000/redoc/
- Postman: [tests/postman_collection.json](../tests/postman_collection.json)