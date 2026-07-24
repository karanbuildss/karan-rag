from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="budget_darpan_audit_logs",
    )
    action = models.CharField(max_length=80, db_index=True)
    object_type = models.CharField(max_length=80)
    object_id = models.CharField(max_length=80)
    before_summary = models.JSONField(default=dict, blank=True)
    after_summary = models.JSONField(default=dict, blank=True)
    request_identifier = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["object_type", "object_id", "created_at"])]

    def __str__(self):
        return f"{self.action} · {self.object_type} {self.object_id}"
