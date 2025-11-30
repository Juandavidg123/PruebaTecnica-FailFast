# API Documentation

Documentación completa de la API REST de FailFast Document Management System.

## Base URL

```
http://localhost:8000/api/
```

## Tabla de Contenidos

- [Autenticación](#autenticación)
- [Companies](#companies)
- [Entities](#entities)
- [Document Types](#document-types)
- [Documents](#documents)
- [Validation Logs](#validation-logs)
- [Códigos de Estado](#códigos-de-estado)
- [Manejo de Errores](#manejo-de-errores)

## Autenticación

La API no requiere autenticación

## Companies

### Listar Empresas

```http
GET /api/companies/
```

**Query Parameters:**
- `is_active` (boolean): Filtrar por estado
- `search` (string): Buscar por nombre o tax_id
- `ordering` (string): Ordenar por campo (ej: `name`, `-created_at`)

**Response:**

```json
{
  "count": 10,
  "next": "http://localhost:8000/api/companies/?page=2",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Empresa Demo",
      "tax_id": "900123456-7",
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Crear Empresa

```http
POST /api/companies/
```

**Request Body:**

```json
{
  "name": "Mi Empresa",
  "tax_id": "900123456-7",
  "is_active": true
}
```

**Response:** `201 Created`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Mi Empresa",
  "tax_id": "900123456-7",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Obtener Detalle de Empresa

```http
GET /api/companies/{id}/
```

**Response:** `200 OK`

### Actualizar Empresa

```http
PUT /api/companies/{id}/
PATCH /api/companies/{id}/
```

**Request Body (PUT - todos los campos):**

```json
{
  "name": "Empresa Actualizada",
  "tax_id": "900123456-7",
  "is_active": true
}
```

**Response:** `200 OK`

### Eliminar Empresa

```http
DELETE /api/companies/{id}/
```

**Response:** `204 No Content`

---

## Entities

### Listar Entidades

```http
GET /api/entities/
```

**Query Parameters:**
- `company` (uuid): Filtrar por empresa
- `entity_type` (string): Filtrar por tipo (`vehicle`, `employee`, `supplier`, `asset`)
- `is_active` (boolean): Filtrar por estado
- `search` (string): Buscar por código o nombre

**Response:**

```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "company": "550e8400-e29b-41d4-a716-446655440000",
      "company_detail": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Mi Empresa",
        "tax_id": "900123456-7"
      },
      "entity_type": "vehicle",
      "entity_type_display": "Vehículo",
      "entity_code": "ABC123",
      "entity_name": "Vehículo ABC123",
      "metadata": {
        "brand": "Toyota",
        "model": "Hilux",
        "year": 2023
      },
      "is_active": true,
      "created_at": "2024-01-15T10:35:00Z"
    }
  ]
}
```

### Crear Entidad

```http
POST /api/entities/
```

**Request Body:**

```json
{
  "company": "550e8400-e29b-41d4-a716-446655440000",
  "entity_type": "vehicle",
  "entity_code": "ABC123",
  "entity_name": "Vehículo ABC123",
  "metadata": {
    "brand": "Toyota",
    "model": "Hilux",
    "year": 2023
  },
  "is_active": true
}
```

**Response:** `201 Created`

---

## Document Types

### Listar Tipos de Documentos

```http
GET /api/document-types/
```

**Query Parameters:**
- `entity_type` (string): Filtrar por tipo de entidad
- `is_mandatory` (boolean): Filtrar por obligatorios
- `uses_n8n_workflow` (boolean): Filtrar por uso de N8N

**Response:**

```json
{
  "count": 3,
  "results": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "code": "SOAT",
      "name": "Seguro Obligatorio",
      "is_mandatory": true,
      "requires_issue_date": true,
      "requires_expiration_date": true,
      "uses_n8n_workflow": false,
      "n8n_webhook_url": null,
      "entity_type": "vehicle",
      "entity_type_display": "Vehículo",
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

### Crear Tipo de Documento

```http
POST /api/document-types/
```

**Request Body:**

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

**Request Body (con N8N):**

```json
{
  "code": "LICENCIA_CONDUCIR",
  "name": "Licencia de Conducción",
  "is_mandatory": true,
  "requires_issue_date": true,
  "requires_expiration_date": true,
  "uses_n8n_workflow": true,
  "n8n_webhook_url": "http://localhost:5678/webhook/validate-license",
  "entity_type": "employee"
}
```

**Response:** `201 Created`

---

## Documents

### Listar Documentos

```http
GET /api/documents/
```

**Query Parameters:**
- `company` (uuid): Filtrar por empresa
- `entity` (uuid): Filtrar por entidad
- `document_type` (uuid): Filtrar por tipo de documento
- `validation_status` (char): Filtrar por estado (`P`, `A`, `R`)

**Response:**

```json
{
  "count": 10,
  "results": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "company": "550e8400-e29b-41d4-a716-446655440000",
      "company_detail": {...},
      "entity": "660e8400-e29b-41d4-a716-446655440001",
      "entity_detail": {...},
      "document_type": "770e8400-e29b-41d4-a716-446655440002",
      "document_type_detail": {...},
      "file_name": "soat_abc123.pdf",
      "file_size": 1024000,
      "mime_type": "application/pdf",
      "s3_bucket": "failfast-docs",
      "s3_key": "companies/550e8400.../vehicles/660e8400.../SOAT_20240115.pdf",
      "s3_region": "us-east-1",
      "issue_date": "2024-01-15",
      "expiration_date": "2025-01-15",
      "validation_status": "A",
      "validation_status_display": "Aprobado",
      "validation_reason": "Documento verificado",
      "uploaded_by": "usuario@ejemplo.com",
      "uploaded_at": "2024-01-15T11:00:00Z",
      "validated_at": "2024-01-15T11:05:00Z",
      "validation_logs": [...]
    }
  ]
}
```

### Cargar Documento

```http
POST /api/documents/upload/
```

**Request (multipart/form-data):**

- `company_id` (uuid): ID de la empresa
- `entity_id` (uuid): ID de la entidad
- `document_type_id` (uuid): ID del tipo de documento
- `file` (file): Archivo a cargar
- `issue_date` (date, opcional): Fecha de emisión (YYYY-MM-DD)
- `expiration_date` (date, opcional): Fecha de vencimiento (YYYY-MM-DD)
- `uploaded_by` (string, opcional): Email del usuario

**cURL Example:**

```bash
curl -X POST http://localhost:8000/api/documents/upload/ \
  -F "company_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "entity_id=660e8400-e29b-41d4-a716-446655440001" \
  -F "document_type_id=770e8400-e29b-41d4-a716-446655440002" \
  -F "file=@soat.pdf" \
  -F "issue_date=2024-01-15" \
  -F "expiration_date=2025-01-15" \
  -F "uploaded_by=usuario@ejemplo.com"
```

**Response:** `201 Created`

```json
{
  "id": "880e8400-e29b-41d4-a716-446655440003",
  "status": "P",
  "message": "Documento cargado exitosamente",
  "n8n_triggered": false
}
```

**Con N8N:**

```json
{
  "id": "880e8400-e29b-41d4-a716-446655440003",
  "status": "P",
  "message": "Documento cargado exitosamente",
  "n8n_triggered": true
}
```

### Descargar Documento

```http
GET /api/documents/{id}/download/
```

**Response:** `200 OK`

```json
{
  "document_id": "880e8400-e29b-41d4-a716-446655440003",
  "file_name": "soat_abc123.pdf",
  "download_url": "https://failfast-docs.s3.amazonaws.com/...",
  "expires_in": 300
}
```

### Aprobar Documento

```http
POST /api/documents/{id}/approve/
```

**Request Body:**

```json
{
  "reason": "Documento verificado manualmente",
  "performed_by": "admin@ejemplo.com"
}
```

**Response:** `200 OK` - Retorna el documento completo actualizado

**Nota:** Solo funciona con documentos que NO usen N8N workflow.

### Rechazar Documento

```http
POST /api/documents/{id}/reject/
```

**Request Body:**

```json
{
  "reason": "Fecha de vencimiento incorrecta",
  "performed_by": "admin@ejemplo.com"
}
```

**Response:** `200 OK` - Retorna el documento completo actualizado

### N8N Callback

```http
POST /api/documents/{id}/n8n-callback/
```

**Request Body (Aprobado):**

```json
{
  "status": "approved",
  "reason": "OCR validado exitosamente",
  "metadata": {
    "ocr_confidence": 0.98,
    "extracted_expiration": "2025-01-15"
  }
}
```

**Request Body (Rechazado):**

```json
{
  "status": "rejected",
  "reason": "OCR no pudo leer el documento",
  "metadata": {
    "error": "low_confidence"
  }
}
```

**Response:** `200 OK` - Retorna el documento completo actualizado

### Validación Masiva

```http
POST /api/documents/validate/
```

**Request Body (Todas las entidades):**

```json
{
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "entity_type": "vehicle",
  "entity_ids": null
}
```

**Request Body (Entidades específicas):**

```json
{
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "entity_type": "vehicle",
  "entity_ids": [
    "660e8400-e29b-41d4-a716-446655440001",
    "660e8400-e29b-41d4-a716-446655440002"
  ]
}
```

**Response:** `200 OK`

```json
{
  "validated_entities": 3,
  "total_errors": 5,
  "errors": [
    {
      "entity_id": "660e8400-e29b-41d4-a716-446655440001",
      "entity_code": "ABC123",
      "document_type_code": "SOAT",
      "error_type": "missing_mandatory",
      "error_message": "Documento obligatorio faltante: Seguro Obligatorio"
    },
    {
      "entity_id": "660e8400-e29b-41d4-a716-446655440001",
      "entity_code": "ABC123",
      "document_type_code": "TECNICOMECANICA",
      "error_type": "expired",
      "error_message": "Documento vencido desde 2024-10-01"
    }
  ]
}
```

**Tipos de Errores:**

- `missing_mandatory`: Documento obligatorio faltante
- `future_issue_date`: Fecha de emisión futura
- `expired`: Documento vencido
- `rejected`: Documento rechazado que requiere reemplazo

---

## Validation Logs

### Listar Logs de Validación

```http
GET /api/validation-logs/
```

**Query Parameters:**
- `document` (uuid): Filtrar por documento
- `action` (string): Filtrar por acción
- `performed_by` (string): Filtrar por usuario

**Response:**

```json
{
  "count": 20,
  "results": [
    {
      "id": "990e8400-e29b-41d4-a716-446655440004",
      "document": "880e8400-e29b-41d4-a716-446655440003",
      "action": "uploaded",
      "action_display": "Cargado",
      "previous_status": null,
      "new_status": "P",
      "reason": "Documento cargado exitosamente",
      "performed_by": "usuario@ejemplo.com",
      "metadata": {},
      "created_at": "2024-01-15T11:00:00Z"
    }
  ]
}
```

### Obtener Detalle de Log

```http
GET /api/validation-logs/{id}/
```

**Response:** `200 OK`

---

## Manejo de Errores

Todos los errores retornan un formato consistente:

```json
{
  "error": true,
  "message": "Descripción del error",
  "details": {
    "field": ["mensaje de error específico"]
  }
}
```

### Ejemplos de Errores

**Validación de Campos:**

```json
{
  "error": true,
  "message": "Invalid input.",
  "details": {
    "tax_id": ["Este campo no puede estar vacío."],
    "name": ["Asegúrese de que este valor no tenga más de 255 caracteres."]
  }
}
```

**Recurso No Encontrado:**

```json
{
  "error": true,
  "message": "Not found.",
  "details": {
    "detail": "No encontrado."
  }
}
```

**Error de Negocio:**

```json
{
  "error": true,
  "message": "El tipo de documento SOAT no aplica para entidades de tipo employee"
}
```

---

## Recursos Adicionales

- **Swagger UI**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/
- **Postman Collection**: [tests/postman_collection.json](../tests/postman_collection.json)
