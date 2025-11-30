from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Company
from .serializers import CompanySerializer


class CompanyViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar empresas.

    list: Listar todas las empresas
    create: Crear una nueva empresa
    retrieve: Obtener detalle de una empresa
    update: Actualizar una empresa
    partial_update: Actualizar parcialmente una empresa
    destroy: Eliminar una empresa
    """
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'tax_id']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']
