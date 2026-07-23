from config.models import DataClassification
from django.db import models
from projects.models import Project


class Contractor(models.Model):
    name = models.CharField(max_length=200)
    registration_number = models.CharField(max_length=80, unique=True, null=True, blank=True)
    municipality_name = models.CharField(max_length=150, blank=True)
    data_classification = models.CharField(
        max_length=40,
        choices=DataClassification.choices,
        default=DataClassification.SYNTHETIC_DEMO,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tender(models.Model):
    class ProcurementMethod(models.TextChoices):
        OPEN = "open_competitive", "Open competitive bidding"
        SEALED_QUOTATION = "sealed_quotation", "Sealed quotation"
        DIRECT = "direct", "Direct procurement"
        OTHER = "other", "Other"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tenders")
    reference = models.CharField(max_length=80, unique=True)
    invitation_number = models.CharField(max_length=80, blank=True, db_index=True)
    title_en = models.CharField(max_length=240)
    title_np = models.CharField(max_length=240)
    procurement_method = models.CharField(max_length=30, choices=ProcurementMethod.choices)
    published_date = models.DateField(null=True, blank=True)
    bid_submission_deadline = models.DateTimeField(null=True, blank=True)
    estimated_amount = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    bid_security_amount = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
    )
    data_note_en = models.CharField(max_length=300, blank=True)
    data_note_np = models.CharField(max_length=300, blank=True)
    source_url = models.URLField(blank=True)
    data_classification = models.CharField(
        max_length=40,
        choices=DataClassification.choices,
        default=DataClassification.SYNTHETIC_DEMO,
    )

    class Meta:
        ordering = ["published_date", "reference"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(estimated_amount__isnull=True)
                | models.Q(estimated_amount__gte=0),
                name="tender_estimated_amount_nonnegative_or_unknown",
            ),
            models.CheckConstraint(
                condition=models.Q(bid_security_amount__isnull=True)
                | models.Q(bid_security_amount__gte=0),
                name="tender_bid_security_nonnegative_or_unknown",
            ),
        ]

    def __str__(self):
        return self.reference


class ContractAward(models.Model):
    tender = models.OneToOneField(Tender, on_delete=models.CASCADE, related_name="award")
    contractor = models.ForeignKey(
        Contractor,
        on_delete=models.PROTECT,
        related_name="contract_awards",
    )
    award_reference = models.CharField(max_length=80, unique=True)
    contract_amount = models.DecimalField(max_digits=18, decimal_places=2)
    awarded_date = models.DateField(null=True, blank=True)
    contract_start_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    source_url = models.URLField(blank=True)
    data_classification = models.CharField(
        max_length=40,
        choices=DataClassification.choices,
        default=DataClassification.SYNTHETIC_DEMO,
    )

    class Meta:
        ordering = ["-awarded_date"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(contract_amount__gte=0),
                name="contract_award_amount_nonnegative",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(contract_start_date__isnull=True)
                    | models.Q(contract_end_date__isnull=True)
                    | models.Q(contract_end_date__gte=models.F("contract_start_date"))
                ),
                name="contract_end_not_before_start",
            ),
        ]

    def __str__(self):
        return self.award_reference

    @property
    def project(self):
        return self.tender.project
