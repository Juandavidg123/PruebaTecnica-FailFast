from django.contrib import admin
from .models import Entity


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ['entity_code', 'entity_name', 'entity_type', 'company', 'is_active', 'created_at']
    list_filter = ['entity_type', 'is_active', 'created_at']
    search_fields = ['entity_code', 'entity_name', 'company__name']
    readonly_fields = ['id', 'created_at']
    autocomplete_fields = ['company']
