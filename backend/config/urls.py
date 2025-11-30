"""
URL configuration for FailFast Document Management System.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="FailFast Document Management API",
        default_version='v1',
        description="""
        Sistema de Gestión de Documentos Empresariales con Validación Automatizada.

        Este API permite:
        - Gestión de documentos para entidades corporativas (vehículos, empleados, proveedores)
        - Almacenamiento en AWS S3
        - Validación automatizada mediante N8N
        - Validaciones masivas con PL/pgSQL
        """,
        terms_of_service="https://www.failfast.com/terms/",
        contact=openapi.Contact(email="api@failfast.com"),
        license=openapi.License(name="Proprietary"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # API endpoints
    path('api/', include('apps.companies.urls')),
    path('api/', include('apps.entities.urls')),
    path('api/', include('apps.documents.urls')),

    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
