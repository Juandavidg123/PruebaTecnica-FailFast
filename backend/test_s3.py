"""
Script para verificar la conexión con AWS S3
"""
import os
import django
import sys

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import boto3
from django.conf import settings
from botocore.exceptions import ClientError

def test_s3_connection():
    """Prueba la conexión con AWS S3"""

    print("=" * 60)
    print("VERIFICACIÓN DE CONFIGURACIÓN AWS S3")
    print("=" * 60)

    # Mostrar configuración
    print(f"Configuración:")
    print(f"   Bucket: {settings.AWS_STORAGE_BUCKET_NAME}")
    print(f"   Region: {settings.AWS_S3_REGION_NAME}")
    print(f"   Access Key ID: {settings.AWS_ACCESS_KEY_ID[:10]}...")

    # Crear cliente S3
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        print(f"Cliente S3 creado exitosamente")
    except Exception as e:
        print(f"Error al crear cliente S3: {e}")
        return False

    # Verificar acceso al bucket
    try:
        response = s3_client.head_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
        print(f"Acceso al bucket '{settings.AWS_STORAGE_BUCKET_NAME}' verificado")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            print(f"El bucket '{settings.AWS_STORAGE_BUCKET_NAME}' no existe")
        elif error_code == '403':
            print(f"No tienes permisos para acceder al bucket '{settings.AWS_STORAGE_BUCKET_NAME}'")
        else:
            print(f"Error al acceder al bucket: {e}")
        return False

    # Listar objetos en el bucket
    try:
        response = s3_client.list_objects_v2(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            MaxKeys=5
        )

        object_count = response.get('KeyCount', 0)
        print(f"Permisos de lectura verificados")
        print(f"   Objetos en el bucket: {object_count}")

        if object_count > 0:
            print(f"\n   Primeros archivos:")
            for obj in response.get('Contents', [])[:5]:
                print(f"   - {obj['Key']} ({obj['Size']} bytes)")
    except ClientError as e:
        print(f"Error al listar objetos: {e}")
        return False

    # Probar escritura (crear archivo de prueba)
    try:
        test_key = "test/connection_test.txt"
        test_content = "Prueba de conexión S3 - FailFast Document Management"

        s3_client.put_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=test_key,
            Body=test_content.encode('utf-8'),
            ContentType='text/plain'
        )
        print(f"Permisos de escritura verificados")
        print(f"   Archivo de prueba creado: {test_key}")

        # Limpiar archivo de prueba
        s3_client.delete_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=test_key
        )
        print(f"Permisos de eliminación verificados")
        print(f"  Archivo de prueba eliminado")

    except ClientError as e:
        print(f"Error al probar escritura/eliminación: {e}")
        return False

    print("\n" + "=" * 60)
    print("¡CONFIGURACIÓN DE S3 EXITOSA!")
    print("=" * 60)
    print("\nTu aplicación está lista para:")
    print("  - Subir documentos a S3")
    print("  - Generar URLs pre-firmadas")
    print("  - Eliminar documentos")
    print("\n")

    return True

if __name__ == '__main__':
    test_s3_connection()
