import uuid

from django.db import models
from projects.models import Project


class AnomalyFlag(models.Model):
    class Severity(models.TextChoices):
        INFO = "info", "Information"
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    class Reliability(models.TextChoices):
        LIMITED = "limited", "Limited evidence"
        MODERATE = "moderate", "Moderate"
        STRONG = "strong", "Strong"
        OFFICIAL_REFERENCE = "official_reference", "Official reference"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        RESOLVED = "resolved", "Resolved"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="anomaly_flags")
    rule_id = models.CharField(max_length=80)
    rule_version = models.PositiveSmallIntegerField(default=1)
    severity = models.CharField(max_length=12, choices=Severity.choices)
    reliability = models.CharField(max_length=24, choices=Reliability.choices)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    title_en = models.CharField(max_length=240)
    title_np = models.CharField(max_length=240)
    reason_en = models.TextField()
    reason_np = models.TextField()
    data_used = models.JSONField(default=dict)
    threshold = models.JSONField(default=dict)
    calculated_values = models.JSONField(default=dict)
    possible_explanations = models.JSONField(default=list)
    recommendation_en = models.TextField()
    recommendation_np = models.TextField()
    source_references = models.JSONField(default=list)
    first_detected_at = models.DateTimeField(auto_now_add=True)
    last_evaluated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-severity", "rule_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "rule_id"],
                name="unique_anomaly_rule_per_project",
            )
        ]
        indexes = [models.Index(fields=["project", "status", "severity"])]

    def __str__(self):
        return f"{self.project} · {self.rule_id}"
