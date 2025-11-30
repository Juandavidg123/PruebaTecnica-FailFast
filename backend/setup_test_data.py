"""
Script para crear datos de prueba para el sistema de documentos
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.companies.models import Company
from apps.entities.models import Entity
from apps.documents.models import DocumentType

print("=" * 60)
print("CONFIGURANDO DATOS DE PRUEBA")
print("=" * 60)

# 1. Crear Empresa
company, created = Company.objects.get_or_create(
    tax_id="900123456-7",
    defaults={
        'name': "Empresa Demo FailFast",
        'is_active': True
    }
)
if created:
    print(f"Empresa creada: {company.name}")
else:
    print(f"Empresa ya existe: {company.name}")
print(f"   ID: {company.id}")

# 2. Crear Entidad (Vehículo)
entity, created = Entity.objects.get_or_create(
    company=company,
    entity_type="vehicle",
    entity_code="ABC123",
    defaults={
        'entity_name': "Vehículo ABC123 - Toyota Hilux",
        'metadata': {
            "brand": "Toyota",
            "model": "Hilux",
            "year": 2023,
            "color": "Blanco"
        }
    }
)
if created:
    print(f"Entidad creada: {entity.entity_name}")
else:
    print(f"Entidad ya existe: {entity.entity_name}")
print(f"   ID: {entity.id}")
print(f"   Tipo: {entity.entity_type}")
print(f"   Código: {entity.entity_code}")

# 3. Crear Tipo de Documento CON N8N
doc_type_n8n, created = DocumentType.objects.get_or_create(
    code="SOAT",
    defaults={
        'name': "Seguro Obligatorio (SOAT)",
        'is_mandatory': True,
        'requires_issue_date': True,
        'requires_expiration_date': True,
        'uses_n8n_workflow': True,
        'n8n_webhook_url': "http://n8n:5678/webhook/validate-document",
        'entity_type': "vehicle"
    }
)
if created:
    print(f"Tipo de documento creado: {doc_type_n8n.name}")
else:
    print(f"Tipo de documento ya existe: {doc_type_n8n.name}")
print(f"   ID: {doc_type_n8n.id}")
print(f"   Usa N8N: {doc_type_n8n.uses_n8n_workflow}")
print(f"   Webhook URL: {doc_type_n8n.n8n_webhook_url}")

# 4. Crear Tipo de Documento SIN N8N (para comparar)
doc_type_manual, created = DocumentType.objects.get_or_create(
    code="LICENCIA",
    defaults={
        'name': "Licencia de Conducción",
        'is_mandatory': True,
        'requires_issue_date': True,
        'requires_expiration_date': True,
        'uses_n8n_workflow': False,
        'entity_type': "employee"
    }
)
if created:
    print(f"Tipo de documento creado: {doc_type_manual.name}")
else:
    print(f"Tipo de documento ya existe: {doc_type_manual.name}")
print(f"   ID: {doc_type_manual.id}")
print(f"   Usa N8N: {doc_type_manual.uses_n8n_workflow}")

print("\n" + "=" * 60)
print("RESUMEN DE IDs PARA USAR EN LA API")
print("=" * 60)
print(f"\nCompany ID:     {company.id}")
print(f"Entity ID:      {entity.id}")
print(f"DocumentType ID (SOAT con N8N): {doc_type_n8n.id}")
print(f"DocumentType ID (Licencia sin N8N): {doc_type_manual.id}")

print("\n" + "=" * 60)
print("EJEMPLO DE CURL PARA SUBIR DOCUMENTO")
print("=" * 60)
print(f"""
curl -X POST http://localhost:8000/api/documents/upload/ \\
  -F "company_id={company.id}" \\
  -F "entity_id={entity.id}" \\
  -F "document_type_id={doc_type_n8n.id}" \\
  -F "file=@documento.pdf" \\
  -F "issue_date=2024-01-15" \\
  -F "expiration_date=2025-01-15" \\
  -F "uploaded_by=admin@failfast.com"
""")

print("Datos de prueba configurados exitosamente")
print("\nAccede a Swagger para probar: http://localhost:8000/swagger/")
print("Accede al Admin: http://localhost:8000/admin/")
print("  Usuario: admin")
print("  Contraseña: (debes configurarla)\n")
