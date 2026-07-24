import uuid

from accounts.models import CitizenProfile
from django.conf import settings
from django.db import models
from projects.models import Project


class CitizenFeedback(models.Model):
    class VerificationStatus(models.TextChoices):
        UNVERIFIED = "unverified", "Unverified citizen"
        VERIFIED = "verified", "Verified citizen"
        VERIFIED_LOCAL = "verified_local", "Verified local resident"

    class ModerationStatus(models.TextChoices):
        PENDING = "pending", "Pending review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    citizen_profile = models.ForeignKey(
        CitizenProfile,
        on_delete=models.CASCADE,
        related_name="feedback",
    )
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="feedback")
    completion_rating = models.PositiveSmallIntegerField()
    quality_rating = models.PositiveSmallIntegerField()
    usefulness_rating = models.PositiveSmallIntegerField()
    allocation_fairness_rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True, max_length=2000)
    directly_observed = models.BooleanField(default=False)
    is_local_resident = models.BooleanField(default=False)
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.UNVERIFIED,
    )
    moderation_status = models.CharField(
        max_length=16,
        choices=ModerationStatus.choices,
        default=ModerationStatus.PENDING,
    )
    idempotency_key = models.CharField(max_length=64, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["citizen_profile", "project"],
                name="one_feedback_per_citizen_project",
                violation_error_code="duplicate_feedback",
            ),
            *[
                models.CheckConstraint(
                    condition=models.Q(**{f"{field}__gte": 1, f"{field}__lte": 5}),
                    name=f"feedback_{field}_between_1_and_5",
                )
                for field in (
                    "completion_rating",
                    "quality_rating",
                    "usefulness_rating",
                    "allocation_fairness_rating",
                )
            ],
        ]
        indexes = [models.Index(fields=["project", "verification_status"])]

    def __str__(self):
        return f"{self.project} · citizen feedback"


class FeedbackRevision(models.Model):
    feedback = models.ForeignKey(
        CitizenFeedback,
        on_delete=models.CASCADE,
        related_name="revisions",
    )
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    before_summary = models.JSONField(default=dict)
    after_summary = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Revision for {self.feedback}"


class ModerationRecord(models.Model):
    feedback = models.ForeignKey(
        CitizenFeedback,
        on_delete=models.CASCADE,
        related_name="moderation_records",
    )
    moderator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    status = models.CharField(max_length=16, choices=CitizenFeedback.ModerationStatus.choices)
    reason = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.feedback} · {self.status}"
