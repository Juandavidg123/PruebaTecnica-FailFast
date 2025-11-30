from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Entity
from .serializers import EntitySerializer


class EntityViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar entidades (vehículos, empleados, proveedores, activos).

    list: Listar todas las entidades
    create: Crear una nueva entidad
    retrieve: Obtener detalle de una entidad
    update: Actualizar una entidad
    partial_update: Actualizar parcialmente una entidad
    destroy: Eliminar una entidad
    """
    queryset = Entity.objects.select_related('company').all()
    serializer_class = EntitySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['company', 'entity_type', 'is_active']
    search_fields = ['entity_code', 'entity_name']
    ordering_fields = ['entity_code', 'entity_name', 'created_at']
    ordering = ['-created_at']
