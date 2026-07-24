import uuid

from budgets.models import BudgetAllocation, FiscalYear, SubSector
from config.models import DataClassification
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from geography.models import LocalGovernment, Ward


class Project(models.Model):
    class Status(models.TextChoices):
        UNKNOWN = "unknown", "Unknown / not evidenced"
        PLANNED = "planned", "Planned"
        PROCUREMENT = "procurement", "Procurement"
        IMPLEMENTATION = "implementation", "Implementation"
        DELAYED = "delayed", "Delayed"
        COMPLETED = "completed", "Completed"
        ON_HOLD = "on_hold", "On hold"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=40, unique=True)
    local_government = models.ForeignKey(
        LocalGovernment,
        on_delete=models.PROTECT,
        related_name="projects",
    )
    ward = models.ForeignKey(
        Ward,
        on_delete=models.PROTECT,
        related_name="projects",
        null=True,
        blank=True,
    )
    fiscal_year = models.ForeignKey(
        FiscalYear,
        on_delete=models.PROTECT,
        related_name="projects",
    )
    subsector = models.ForeignKey(
        SubSector,
        on_delete=models.PROTECT,
        related_name="projects",
    )
    budget_allocation = models.ForeignKey(
        BudgetAllocation,
        on_delete=models.PROTECT,
        related_name="projects",
        null=True,
        blank=True,
    )
    title_en = models.CharField(max_length=240)
    title_np = models.CharField(max_length=240)
    description_en = models.TextField(blank=True)
    description_np = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices)
    allocated_amount = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
    )
    official_progress_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )
    planned_start_date = models.DateField(null=True, blank=True)
    planned_end_date = models.DateField(null=True, blank=True)
    data_classification = models.CharField(
        max_length=40,
        choices=DataClassification.choices,
        default=DataClassification.SYNTHETIC_DEMO,
    )
    data_note_en = models.CharField(max_length=300, blank=True)
    data_note_np = models.CharField(max_length=300, blank=True)
    source_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fiscal_year__code", "title_en"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(allocated_amount__isnull=True)
                | models.Q(allocated_amount__gte=0),
                name="project_allocated_amount_nonnegative_or_unknown",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(official_progress_percent__isnull=True)
                    | models.Q(
                        official_progress_percent__gte=0,
                        official_progress_percent__lte=100,
                    )
                ),
                name="project_progress_between_0_and_100_or_unknown",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(planned_start_date__isnull=True)
                    | models.Q(planned_end_date__isnull=True)
                    | models.Q(planned_end_date__gte=models.F("planned_start_date"))
                ),
                name="project_end_not_before_start",
            ),
        ]
        indexes = [
            models.Index(fields=["local_government", "fiscal_year", "status"]),
            models.Index(fields=["subsector", "status"]),
        ]

    def __str__(self):
        return self.title_en

    def clean(self):
        errors = {}
        if self.ward_id and self.local_government_id:
            if self.ward.local_government_id != self.local_government_id:
                errors["ward"] = "Ward must belong to the project's local government."
        if self.budget_allocation_id:
            allocation = self.budget_allocation
            if allocation.local_government_id != self.local_government_id:
                errors["budget_allocation"] = (
                    "Budget allocation must belong to the same local government."
                )
            elif allocation.fiscal_year_id != self.fiscal_year_id:
                errors["budget_allocation"] = "Budget allocation must use the same fiscal year."
            elif allocation.subsector_id != self.subsector_id:
                errors["budget_allocation"] = "Budget allocation must use the same subsector."
        if errors:
            raise ValidationError(errors)


class ProjectLocation(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name="location")
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    label_en = models.CharField(max_length=200, blank=True)
    label_np = models.CharField(max_length=200, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(latitude__gte=-90, latitude__lte=90),
                name="project_latitude_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(longitude__gte=-180, longitude__lte=180),
                name="project_longitude_valid",
            ),
        ]

    def __str__(self):
        return self.label_en or str(self.project)


class ProjectMilestone(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Not started"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        DELAYED = "delayed", "Delayed"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="milestones")
    sequence = models.PositiveSmallIntegerField()
    title_en = models.CharField(max_length=200)
    title_np = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=Status.choices)
    progress_percent = models.DecimalField(max_digits=5, decimal_places=2)
    planned_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "sequence"],
                name="unique_project_milestone_sequence",
            ),
            models.CheckConstraint(
                condition=models.Q(progress_percent__gte=0, progress_percent__lte=100),
                name="milestone_progress_between_0_and_100",
            ),
        ]

    def __str__(self):
        return f"{self.project} · {self.title_en}"


class ProjectEvidenceEvent(models.Model):
    """A dated official process event that does not imply a financial amount.

    Municipal reports sometimes publish an agreement, monitoring, or payment
    date without publishing the corresponding contract value, payment amount,
    or physical progress percentage. Keeping the event separate prevents a
    known date from being presented as a known amount.
    """

    class EventType(models.TextChoices):
        AGREEMENT_RECORDED = "agreement_recorded", "Agreement recorded"
        MONITORING_RECORDED = "monitoring_recorded", "Monitoring recorded"
        PAYMENT_DATE_RECORDED = "payment_date_recorded", "Payment date recorded"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="evidence_events",
    )
    event_type = models.CharField(max_length=30, choices=EventType.choices)
    date_bs = models.CharField(
        max_length=10,
        validators=[
            RegexValidator(
                regex=r"^\d{4}/\d{2}/\d{2}$",
                message="BS date must use YYYY/MM/DD format.",
            )
        ],
    )
    date_ad = models.DateField(null=True, blank=True)
    source_page = models.PositiveIntegerField()
    source_url = models.URLField(blank=True)
    note_en = models.CharField(max_length=240, blank=True)
    note_np = models.CharField(max_length=240, blank=True)
    data_classification = models.CharField(
        max_length=40,
        choices=DataClassification.choices,
        default=DataClassification.OFFICIAL,
    )

    class Meta:
        ordering = ["source_page", "event_type", "date_bs"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "event_type", "date_bs"],
                name="unique_project_evidence_event_date",
            ),
            models.CheckConstraint(
                condition=models.Q(source_page__gte=1),
                name="project_evidence_event_source_page_positive",
            ),
        ]
        indexes = [models.Index(fields=["project", "event_type"])]

    def __str__(self):
        return f"{self.project} · {self.get_event_type_display()} · {self.date_bs} BS"
