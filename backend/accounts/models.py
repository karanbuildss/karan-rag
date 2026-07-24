from django.conf import settings
from django.db import models


class CitizenProfile(models.Model):
    class Role(models.TextChoices):
        CITIZEN = "citizen", "Citizen"
        VERIFIED_CITIZEN = "verified_citizen", "Verified citizen"
        OFFICIAL = "official", "Official"
        MODERATOR = "moderator", "Moderator"
        SYSTEM_ADMIN = "system_admin", "System administrator"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="citizen_profile",
    )
    role = models.CharField(max_length=24, choices=Role.choices, default=Role.CITIZEN)
    citizen_key = models.CharField(max_length=64, unique=True, null=True, blank=True)
    verified_municipality_code = models.CharField(max_length=20, blank=True)
    verified_ward_number = models.PositiveSmallIntegerField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} · {self.role}"

    @property
    def is_identity_verified(self):
        return bool(self.citizen_key and self.verified_at)


class VerificationRecord(models.Model):
    class Status(models.TextChoices):
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"

    profile = models.ForeignKey(
        CitizenProfile,
        on_delete=models.CASCADE,
        related_name="verification_records",
    )
    issuer = models.CharField(max_length=160)
    subject_key = models.CharField(max_length=64)
    token_identifier_hash = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=16, choices=Status.choices)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.profile} · {self.status}"
