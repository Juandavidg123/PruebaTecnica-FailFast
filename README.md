# FailFast Document Management System

Sistema de gestión de documentos con validación automatizada.

## Stack

Python 3.11 • Django 5.0 • PostgreSQL 17 • Docker • AWS S3 • N8N

## Qué hace

- Gestión de documentos para empresas y sus entidades (vehículos, empleados, etc.)
- Archivos guardados en AWS S3 con URLs temporales
- Validación automática via N8N webhooks (opcional)
- Validación masiva de documentos con PL/pgSQL
- API REST documentada con Swagger

### Cómo funciona

1. Cliente sube documento vía API
2. Se guarda en AWS S3
3. Metadatos se guardan en PostgreSQL
4. Si aplica, se dispara webhook a N8N para validación
5. N8N retorna el resultado
6. Todo se registra en logs de auditoría

## Tecnologías

**Backend:** Django 5.0.1, Django REST Framework 3.14, PostgreSQL 17

**Externos:** AWS S3, N8N

**DevOps:** Docker, Gunicorn

**Tests:** pytest, factory-boy

## Setup

Necesitas Docker y cuenta AWS S3 junto a N8N.

```bash
# 1. Copiar variables de entorno
cp .env.example .env

# 2. Editar .env con tus credenciales AWS y configs

# 3. Levantar servicios
cd docker
docker-compose up --build

# 4. Migraciones
docker-compose exec web python manage.py migrate

# 5. Crear superusuario
docker-compose exec web python manage.py createsuperuser
```

URLs disponibles:
- API: http://localhost:8000/api/
- Admin: http://localhost:8000/admin/
- Swagger: http://localhost:8000/swagger/

### Configurar N8N

Si quieres usar validación automática:
1. Instalar: `npm install -g n8n`
2. Ejecutar: `n8n start`
3. Importar workflow de `docs/n8n-workflow.json` en caso dado de que se tenga una suscripción AWS o `docs/n8n-workflow-simple.json` para una versión sin AWS.
4. Configurar webhook URL en tipos de documentos

## Uso rápido

Ejemplos básicos (ver docs/API.md para más detalles):

```bash
# Crear empresa
curl -X POST http://localhost:8000/api/companies/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Mi Empresa", "tax_id": "900123456-7"}'

# Subir documento
curl -X POST http://localhost:8000/api/documents/upload/ \
  -F "company_id=UUID" \
  -F "entity_id=UUID" \
  -F "document_type_id=UUID" \
  -F "file=@documento.pdf"

# Validación masiva
curl -X POST http://localhost:8000/api/documents/validate/ \
  -H "Content-Type: application/json" \
  -d '{"company_id": "UUID", "entity_type": "vehicle"}'
```

## API

Endpoints principales:
- `/api/companies/` - CRUD empresas
- `/api/entities/` - CRUD entidades (vehículos, empleados, etc.)
- `/api/document-types/` - CRUD tipos de documentos
- `/api/documents/upload/` - Subir documento
- `/api/documents/{id}/approve/` - Aprobar
- `/api/documents/validate/` - Validación masiva
- `/api/validation-logs/` - Ver logs de auditoría

Docs completas: [docs/API.md](docs/API.md) o Swagger en `/swagger/`

## Tests

```bash
# Correr todos
docker-compose exec web pytest

# Con cobertura
docker-compose exec web pytest --cov=apps --cov-report=html
```

Cobertura >70% en modelos, servicios y endpoints.

## Base de datos

**Modelos:** Company, Entity, DocumentType, Document, DocumentValidationLog

**Función PL/pgSQL:** `fn_validate_documents_bulk` - Valida masivamente documentos obligatorios faltantes, vencidos, rechazados, etc.

Ver: [sql/fn_validate_documents_bulk.sql](sql/fn_validate_documents_bulk.sql)

## Postman

Importar `docs/failfast-api.postman_collection.json`. Crear entorno con `base_url = http://localhost:8000`

## Docs

- [API.md](docs/API.md) - Todos los endpoints
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Decisiones de diseño
- [n8n-workflow.json](docs/n8n-workflow.json) - Workflow N8N con Suscripción AWS
- [n8n-workflow-simple.json](docs/n8n-workflow-simple.json) - Workflow N8N sin AWS

---

Juan David - Prueba Técnica Backend FailFast