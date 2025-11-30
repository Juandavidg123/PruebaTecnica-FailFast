"""
Utility functions for document management.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler para DRF que retorna errores en formato consistente.
    """
    response = exception_handler(exc, context)

    if response is not None:
        custom_response_data = {
            'error': True,
            'message': str(exc),
            'details': response.data if isinstance(response.data, dict) else {'detail': response.data}
        }
        response.data = custom_response_data

    return response


def validate_file_type(file_obj, allowed_types=None):
    """
    Valida el tipo de archivo.

    Args:
        file_obj: Objeto de archivo
        allowed_types: Lista de tipos MIME permitidos

    Returns:
        bool: True si es válido

    Raises:
        ValueError: Si el tipo no es permitido
    """
    if allowed_types is None:
        allowed_types = [
            'application/pdf',
            'image/jpeg',
            'image/png',
            'image/jpg',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ]

    content_type = file_obj.content_type if hasattr(file_obj, 'content_type') else None

    if content_type not in allowed_types:
        raise ValueError(
            f"Tipo de archivo no permitido: {content_type}. "
            f"Tipos permitidos: {', '.join(allowed_types)}"
        )

    return True


def validate_file_size(file_obj, max_size_mb=10):
    """
    Valida el tamaño del archivo.

    Args:
        file_obj: Objeto de archivo
        max_size_mb: Tamaño máximo en MB

    Returns:
        bool: True si es válido

    Raises:
        ValueError: Si el tamaño excede el límite
    """
    max_size_bytes = max_size_mb * 1024 * 1024

    if file_obj.size > max_size_bytes:
        raise ValueError(
            f"El archivo excede el tamaño máximo permitido de {max_size_mb}MB. "
            f"Tamaño actual: {file_obj.size / (1024 * 1024):.2f}MB"
        )

    return True
