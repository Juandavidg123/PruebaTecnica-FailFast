"""
Script to populate the database with demo data for testing.
Run with: python manage.py shell < setup_demo_data.py
Or: docker-compose exec web python setup_demo_data.py
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.companies.models import Company
from apps.entities.models import Entity
from apps.documents.models import DocumentType

def create_demo_data():
    print("Creating demo data...")
    print("=" * 50)

    # Create companies
    print("Creating companies...")
    companies = []
    company_data = [
        {"name": "Transportes del Norte S.A.", "tax_id": "900123456-1"},
        {"name": "Logística Express Ltda.", "tax_id": "900234567-2"},
    ]

    for data in company_data:
        company, created = Company.objects.get_or_create(
            tax_id=data["tax_id"],
            defaults={"name": data["name"], "is_active": True}
        )
        companies.append(company)
        status = "Created" if created else "Already exists"
        print(f"  {status}: {company.name} (ID: {company.id})")

    # Create vehicle document types
    print("Creating vehicle document types...")
    vehicle_doc_types = [
        {
            "code": "SOAT",
            "name": "Seguro Obligatorio de Accidentes de Tránsito",
            "is_mandatory": True,
            "requires_issue_date": True,
            "requires_expiration_date": True,
            "entity_type": "vehicle"
        },
        {
            "code": "TECNICOMECANICA",
            "name": "Revisión Técnico-Mecánica",
            "is_mandatory": True,
            "requires_issue_date": True,
            "requires_expiration_date": True,
            "entity_type": "vehicle"
        },
        {
            "code": "TARJETA_PROPIEDAD",
            "name": "Tarjeta de Propiedad",
            "is_mandatory": True,
            "requires_issue_date": False,
            "requires_expiration_date": False,
            "entity_type": "vehicle"
        },
        {
            "code": "POLIZA_TODO_RIESGO",
            "name": "Póliza de Seguro Todo Riesgo",
            "is_mandatory": False,
            "requires_issue_date": True,
            "requires_expiration_date": True,
            "entity_type": "vehicle"
        },
    ]

    for data in vehicle_doc_types:
        doc_type, created = DocumentType.objects.get_or_create(
            code=data["code"],
            defaults=data
        )
        status = "Created" if created else "Already exists"
        print(f"  {status}: {doc_type.name}")

    # Create employee document types
    print("Creating employee document types...")
    employee_doc_types = [
        {
            "code": "LICENCIA_CONDUCIR",
            "name": "Licencia de Conducir",
            "is_mandatory": True,
            "requires_issue_date": True,
            "requires_expiration_date": True,
            "entity_type": "employee"
        },
        {
            "code": "CEDULA",
            "name": "Cédula de Ciudadanía",
            "is_mandatory": True,
            "requires_issue_date": True,
            "requires_expiration_date": False,
            "entity_type": "employee"
        },
        {
            "code": "EPS",
            "name": "Afiliación a EPS",
            "is_mandatory": True,
            "requires_issue_date": True,
            "requires_expiration_date": False,
            "entity_type": "employee"
        },
        {
            "code": "ARL",
            "name": "Afiliación a ARL",
            "is_mandatory": True,
            "requires_issue_date": True,
            "requires_expiration_date": False,
            "entity_type": "employee"
        },
    ]

    for data in employee_doc_types:
        doc_type, created = DocumentType.objects.get_or_create(
            code=data["code"],
            defaults=data
        )
        status = "Created" if created else "Already exists"
        print(f"  {status}: {doc_type.name}")

    # Create vehicles
    print("Creating vehicles...")
    vehicles = []
    vehicle_data = [
        {
            "entity_code": "ABC123",
            "entity_name": "Camión Hino FC 2023",
            "metadata": {
                "brand": "Hino",
                "model": "FC",
                "year": 2023,
                "capacity": "7 toneladas"
            }
        },
        {
            "entity_code": "DEF456",
            "entity_name": "Camioneta Chevrolet D-MAX",
            "metadata": {
                "brand": "Chevrolet",
                "model": "D-MAX",
                "year": 2022,
                "capacity": "1 tonelada"
            }
        },
        {
            "entity_code": "GHI789",
            "entity_name": "Tracto Freightliner",
            "metadata": {
                "brand": "Freightliner",
                "model": "Cascadia",
                "year": 2021,
                "capacity": "40 toneladas"
            }
        },
    ]

    for company in companies[:1]:  # Use first company
        for data in vehicle_data:
            vehicle, created = Entity.objects.get_or_create(
                company=company,
                entity_type="vehicle",
                entity_code=data["entity_code"],
                defaults={
                    "entity_name": data["entity_name"],
                    "metadata": data["metadata"],
                    "is_active": True
                }
            )
            vehicles.append(vehicle)
            status = "Created" if created else "Already exists"
            print(f"  {status}: {vehicle.entity_code} - {vehicle.entity_name}")

    # Create employees
    print("Creating employees...")
    employee_data = [
        {
            "entity_code": "1234567890",
            "entity_name": "Juan Pérez García",
            "metadata": {
                "position": "Conductor",
                "phone": "3001234567",
                "email": "juan.perez@example.com"
            }
        },
        {
            "entity_code": "0987654321",
            "entity_name": "María González López",
            "metadata": {
                "position": "Conductora",
                "phone": "3009876543",
                "email": "maria.gonzalez@example.com"
            }
        },
    ]

    for company in companies[:1]:  # Use first company
        for data in employee_data:
            employee, created = Entity.objects.get_or_create(
                company=company,
                entity_type="employee",
                entity_code=data["entity_code"],
                defaults={
                    "entity_name": data["entity_name"],
                    "metadata": data["metadata"],
                    "is_active": True
                }
            )
            status = "Created" if created else "Already exists"
            print(f"  {status}: {employee.entity_code} - {employee.entity_name}")

    # Summary
    print("\n" + "=" * 50)
    print("Demo data creation complete!")
    print("=" * 50)
    print(f"\nSummary:")
    print(f"  - Companies: {Company.objects.count()}")
    print(f"  - Document Types: {DocumentType.objects.count()}")
    print(f"  - Entities (Total): {Entity.objects.count()}")
    print(f"  - Vehicles: {Entity.objects.filter(entity_type='vehicle').count()}")
    print(f"  - Employees: {Entity.objects.filter(entity_type='employee').count()}")

    print(f"\nImportant IDs for testing:")
    if companies:
        print(f"  - Company ID: {companies[0].id}")
    if vehicles:
        print(f"  - Vehicle ID: {vehicles[0].id}")

    soat = DocumentType.objects.filter(code="SOAT").first()
    if soat:
        print(f"  - SOAT Document Type ID: {soat.id}")

    print("\nNext steps:")
    print("  1. Access API: http://localhost:8000/api/")
    print("  2. Access Swagger: http://localhost:8000/swagger/")
    print("  3. Upload a document using the IDs above")
    print("  4. Test bulk validation: POST /api/documents/validate/")
    print("\nReady to test!")

if __name__ == "__main__":
    try:
        create_demo_data()
    except Exception as e:
        print(f"\nError creating demo data: {e}")
        import traceback
        traceback.print_exc()
