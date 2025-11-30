# FailFast Document Management System

Sistema de Gestión de Documentos Empresariales con Validación Automatizada

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Django](https://img.shields.io/badge/Django-5.0-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-blue)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)

## Tabla de Contenidos

- [Características](#características)
- [Arquitectura](#arquitectura)
- [Tecnologías](#tecnologías)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [API Endpoints](#api-endpoints)
- [Tests](#tests)
- [Base de Datos](#base-de-datos)
- [Contribuir](#contribuir)

## Características

- **Gestión completa de documentos** para entidades corporativas
- **Almacenamiento en AWS S3** con URLs pre-firmadas seguras
- **Validación automatizada** mediante integración con N8N workflows
- **Validaciones masivas eficientes** con funciones PL/pgSQL
- **API REST completa** documentada con Swagger/OpenAPI
- **Sistema de auditoría** completo con logs de validación
- **Docker y Docker Compose** para desarrollo y producción
- **Tests comprehensivos** con >70% de cobertura

### Flujo de Trabajo

1. **Carga de Documento**: Cliente sube documento vía API
2. **Almacenamiento**: Archivo se guarda en AWS S3
3. **Metadatos**: Información del documento se guarda en PostgreSQL
4. **Validación N8N**: Si el tipo de documento lo requiere, se dispara un webhook a N8N
5. **Callback**: N8N procesa el documento y retorna resultado
6. **Auditoría**: Todos los cambios se registran en logs de validación

## Tecnologías

### Backend
- **Django 5.0.1** - Framework web
- **Django REST Framework 3.14** - API REST
- **PostgreSQL 17** - Base de datos
- **PL/pgSQL** - Funciones de base de datos

### Servicios Externos
- **AWS S3** - Almacenamiento de archivos
- **N8N** - Orquestación de workflows

### DevOps
- **Docker & Docker Compose** - Contenedorización
- **Gunicorn** - Servidor WSGI
- **WhiteNoise** - Archivos estáticos

### Testing
- **pytest** - Framework de testing
- **pytest-django** - Plugin Django para pytest
- **factory-boy** - Factories para testing
- **pytest-cov** - Cobertura de código

## Instalación

### Prerrequisitos

- Docker y Docker Compose instalados
- Cuenta de AWS con acceso a S3
- N8N instalado (opcional, para testing completo)

### 1. Clonar el Repositorio

```bash
git clone https://github.com/failfast/document-management.git
cd document-management
```

### 2. Configurar Variables de Entorno

```bash
cp .env.example .env
```

Editar `.env` con tus credenciales:

```env
# Django Settings
SECRET_KEY=tu-secret-key-aqui-cambiar-en-produccion
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=tu-postgresql-connection-string

# AWS S3
AWS_ACCESS_KEY_ID=tu-access-key-id
AWS_SECRET_ACCESS_KEY=tu-secret-access-key
AWS_STORAGE_BUCKET_NAME=tu-servicio-bucket
AWS_S3_REGION_NAME=tu-region

# N8N Integration
N8N_BASE_URL=http://localhost:5678
N8N_API_KEY=tu-n8n-api-key

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

### 3. Levantar con Docker

```bash
cd docker
docker-compose up --build
```

### 4. Aplicar Migraciones

```bash
docker-compose exec web python manage.py migrate
```

### 5. Crear Función PL/pgSQL

```bash
docker-compose exec db psql -U failfast -d failfast_db -f /docker-entrypoint-initdb.d/fn_validate_documents_bulk.sql
```

### 6. Crear Superusuario

```bash
docker-compose exec web python manage.py createsuperuser
```

### 7. Acceder a la Aplicación

- **API**: http://localhost:8000/api/
- **Admin**: http://localhost:8000/admin/
- **Swagger**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/

## Configuración

### Configurar AWS S3

1. Crear un bucket en AWS S3
2. Configurar permisos IAM con acceso al bucket
3. Agregar las credenciales en `.env`

### Configurar N8N (Opcional)

1. Instalar N8N: `npm install -g n8n`
2. Ejecutar N8N: `n8n start`
3. Importar el workflow de ejemplo: `docs/n8n-workflow.json`
4. Configurar webhook URL en los tipos de documentos

## Uso

### Crear una Empresa

```bash
curl -X POST http://localhost:8000/api/companies/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mi Empresa",
    "tax_id": "900123456-7",
    "is_active": true
  }'
```

### Crear una Entidad (Vehículo)

```bash
curl -X POST http://localhost:8000/api/entities/ \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "UUID_DE_LA_EMPRESA",
    "entity_type": "vehicle",
    "entity_code": "ABC123",
    "entity_name": "Vehículo ABC123",
    "metadata": {
      "brand": "Toyota",
      "model": "Hilux",
      "year": 2023
    }
  }'
```

### Crear un Tipo de Documento

```bash
curl -X POST http://localhost:8000/api/document-types/ \
  -H "Content-Type: application/json" \
  -d '{
    "code": "SOAT",
    "name": "Seguro Obligatorio",
    "is_mandatory": true,
    "requires_issue_date": true,
    "requires_expiration_date": true,
    "uses_n8n_workflow": false,
    "entity_type": "vehicle"
  }'
```

### Cargar un Documento

```bash
curl -X POST http://localhost:8000/api/documents/upload/ \
  -F "company_id=UUID_DE_LA_EMPRESA" \
  -F "entity_id=UUID_DE_LA_ENTIDAD" \
  -F "document_type_id=UUID_DEL_TIPO_DOC" \
  -F "file=@/ruta/al/documento.pdf" \
  -F "issue_date=2024-01-15" \
  -F "expiration_date=2025-01-15" \
  -F "uploaded_by=usuario@ejemplo.com"
```

### Aprobar un Documento

```bash
curl -X POST http://localhost:8000/api/documents/{ID}/approve/ \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Documento verificado manualmente",
    "performed_by": "admin@ejemplo.com"
  }'
```

### Validación Masiva

```bash
curl -X POST http://localhost:8000/api/documents/validate/ \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "UUID_DE_LA_EMPRESA",
    "entity_type": "vehicle",
    "entity_ids": null
  }'
```

## API Endpoints

### Companies

- `GET /api/companies/` - Listar empresas
- `POST /api/companies/` - Crear empresa
- `GET /api/companies/{id}/` - Detalle de empresa
- `PUT /api/companies/{id}/` - Actualizar empresa
- `DELETE /api/companies/{id}/` - Eliminar empresa

### Entities

- `GET /api/entities/` - Listar entidades
- `POST /api/entities/` - Crear entidad
- `GET /api/entities/{id}/` - Detalle de entidad
- `PUT /api/entities/{id}/` - Actualizar entidad
- `DELETE /api/entities/{id}/` - Eliminar entidad

### Document Types

- `GET /api/document-types/` - Listar tipos de documentos
- `POST /api/document-types/` - Crear tipo de documento
- `GET /api/document-types/{id}/` - Detalle de tipo
- `PUT /api/document-types/{id}/` - Actualizar tipo
- `DELETE /api/document-types/{id}/` - Eliminar tipo

### Documents

- `GET /api/documents/` - Listar documentos
- `POST /api/documents/upload/` - Cargar documento
- `GET /api/documents/{id}/` - Detalle de documento
- `GET /api/documents/{id}/download/` - Descargar documento
- `POST /api/documents/{id}/approve/` - Aprobar documento
- `POST /api/documents/{id}/reject/` - Rechazar documento
- `POST /api/documents/{id}/n8n-callback/` - Callback de N8N
- `POST /api/documents/validate/` - Validación masiva

### Validation Logs

- `GET /api/validation-logs/` - Listar logs
- `GET /api/validation-logs/{id}/` - Detalle de log

Ver documentación completa en: [docs/API.md](docs/API.md)

## Tests

### Ejecutar Tests

```bash
# Todos los tests
docker-compose exec web pytest

# Con cobertura
docker-compose exec web pytest --cov=apps --cov-report=html

# Tests específicos
docker-compose exec web pytest apps/documents/tests/test_models.py
```

### Cobertura Actual

El proyecto mantiene >70% de cobertura de código con tests para:

- Modelos y validaciones
- Serializers
- Servicios (S3, N8N, Validaciones)
- API endpoints
- Integración con servicios externos

## Base de Datos

### Modelos Principales

1. **Company** - Empresas
2. **Entity** - Entidades (vehículos, empleados, etc.)
3. **DocumentType** - Tipos de documentos
4. **Document** - Documentos
5. **DocumentValidationLog** - Logs de auditoría

### Función PL/pgSQL

**fn_validate_documents_bulk**: Valida documentos de manera masiva

```sql
SELECT * FROM fn_validate_documents_bulk(
    'company_uuid'::uuid,
    'vehicle',
    NULL  -- NULL = todas las entidades
);
```

Validaciones:
- Documentos obligatorios faltantes
- Fechas de emisión futuras
- Documentos vencidos
- Documentos rechazados

Ver documentación completa en: [sql/fn_validate_documents_bulk.sql](sql/fn_validate_documents_bulk.sql)

## Postman
- Para probar la colección de API, importar el archivo `docs/failfast-api.postman_collection.json` en Postman.
- Se debe crear un entorno con las variable correspondiente key: base_url value: http://localhost:8000.

## Documentación Adicional

- [API Documentation](docs/API.md) - Documentación detallada de endpoints
- [Architecture](docs/ARCHITECTURE.md) - Decisiones de arquitectura
- [N8N Workflow AWS](docs/n8n-workflow.json) - Workflow de ejemplo para N8N con credenciales AWS (Subscripción)
- [N8N Workflow Simple](docs/n8n-workflow-simple.json) - Workflow de ejemplo para N8N sin credenciales AWS (Capa gratuita)

## Autor
Juan David - Desarrollado para FailFast - Prueba Técnica Backend


