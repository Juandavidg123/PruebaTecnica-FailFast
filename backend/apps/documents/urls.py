from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentTypeViewSet, DocumentViewSet, DocumentValidationLogViewSet

router = DefaultRouter()
router.register(r'document-types', DocumentTypeViewSet, basename='document-type')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'validation-logs', DocumentValidationLogViewSet, basename='validation-log')

urlpatterns = [
    path('', include(router.urls)),
]
