"""
Entity models for FailFast Document Management System.
"""
import uuid
from django.db import models
from apps.companies.models import Company


class Entity(models.Model):
    """
    Entidad genérica que puede representar vehículos, empleados, proveedores, etc.

    Attributes:
        id: Identificador único UUID
        company: Empresa a la que pertenece la entidad
        entity_type: Tipo de entidad (vehicle, employee, supplier)
        entity_code: Código único de la entidad (placa, cédula, NIT, etc.)
        entity_name: Nombre descriptivo de la entidad
        metadata: Datos adicionales en formato JSON
        is_active: Estado de la entidad
        created_at: Fecha de creación
    """
    ENTITY_TYPE_CHOICES = [
        ('vehicle', 'Vehículo'),
        ('employee', 'Empleado'),
        ('supplier', 'Proveedor'),
        ('asset', 'Activo'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='entities',
        verbose_name='Empresa'
    )
    entity_type = models.CharField(
        max_length=50,
        choices=ENTITY_TYPE_CHOICES,
        verbose_name='Tipo de entidad'
    )
    entity_code = models.CharField(max_length=100, verbose_name='Código')
    entity_name = models.CharField(max_length=255, verbose_name='Nombre')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='Metadatos')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')

    class Meta:
        db_table = 'entities'
        verbose_name = 'Entidad'
        verbose_name_plural = 'Entidades'
        ordering = ['-created_at']
        unique_together = ['company', 'entity_type', 'entity_code']
        indexes = [
            models.Index(fields=['company', 'entity_type']),
            models.Index(fields=['entity_code']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.get_entity_type_display()} - {self.entity_code}: {self.entity_name}"
