"""
Constants for Document Management System.
Centralizes magic strings and literals to improve maintainability.
"""


class ValidationStatus:
    """Document validation status constants."""
    PENDING = 'P'
    APPROVED = 'A'
    REJECTED = 'R'

    CHOICES = [
        (PENDING, 'Pendiente'),
        (APPROVED, 'Aprobado'),
        (REJECTED, 'Rechazado'),
    ]


class DocumentAction:
    """Document action types for audit logging."""
    UPLOADED = 'uploaded'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    N8N_SENT = 'n8n_sent'
    N8N_CALLBACK = 'n8n_callback'

    CHOICES = [
        (UPLOADED, 'Cargado'),
        (APPROVED, 'Aprobado'),
        (REJECTED, 'Rechazado'),
        (N8N_SENT, 'Enviado a N8N'),
        (N8N_CALLBACK, 'Respuesta de N8N'),
    ]


class EntityType:
    """Entity type constants."""
    VEHICLE = 'vehicle'
    EMPLOYEE = 'employee'
    SUPPLIER = 'supplier'
    ASSET = 'asset'

    CHOICES = [
        (VEHICLE, 'Vehículo'),
        (EMPLOYEE, 'Empleado'),
        (SUPPLIER, 'Proveedor'),
        (ASSET, 'Activo'),
    ]


class N8NStatus:
    """N8N callback status constants."""
    APPROVED = 'approved'
    REJECTED = 'rejected'
