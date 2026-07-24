from django.contrib import admin

from audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "object_type", "object_id", "actor", "created_at")
    list_filter = ("action", "object_type")
    readonly_fields = [field.name for field in AuditLog._meta.fields]
