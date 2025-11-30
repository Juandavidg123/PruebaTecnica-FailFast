"""
Company models for FailFast Document Management System.
"""
import uuid
from django.db import models


class Company(models.Model):
    """
    Empresa que utiliza el sistema de gestión documental.

    Attributes:
        id: Identificador único UUID
        name: Nombre de la empresa
        tax_id: NIT o identificación tributaria (único)
        is_active: Estado de la empresa
        created_at: Fecha de creación
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name='Nombre')
    tax_id = models.CharField(max_length=50, unique=True, verbose_name='NIT')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')

    class Meta:
        db_table = 'companies'
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tax_id']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.tax_id})"
