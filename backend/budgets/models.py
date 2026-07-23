from config.models import DataClassification
from django.db import models
from geography.models import LocalGovernment


class FiscalYear(models.Model):
    code = models.CharField(max_length=12, unique=True, help_text="Stable API code, e.g. 2081-82")
    year_bs = models.CharField(max_length=12, unique=True, help_text="Bikram Sambat, e.g. 2081/82")
    year_ad = models.CharField(max_length=12, unique=True, help_text="Gregorian, e.g. 2024/25")
    label_np = models.CharField(max_length=100)

    class Meta:
        ordering = ["-code"]

    def __str__(self):
        return self.year_bs


class Sector(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name_en = models.CharField(max_length=150)
    name_np = models.CharField(max_length=150)

    class Meta:
        ordering = ["name_en"]

    def __str__(self):
        return self.name_en


class SubSector(models.Model):
    code = models.CharField(max_length=30, unique=True)
    sector = models.ForeignKey(Sector, on_delete=models.PROTECT, related_name="subsectors")
    name_en = models.CharField(max_length=150)
    name_np = models.CharField(max_length=150)

    class Meta:
        ordering = ["sector__name_en", "name_en"]

    def __str__(self):
        return self.name_en


class BudgetAllocation(models.Model):
    class BudgetType(models.TextChoices):
        RECURRENT = "recurrent", "Recurrent"
        CAPITAL = "capital", "Capital"
        FINANCING = "financing", "Financing"

    local_government = models.ForeignKey(
        LocalGovernment,
        on_delete=models.PROTECT,
        related_name="budget_allocations",
    )
    fiscal_year = models.ForeignKey(
        FiscalYear,
        on_delete=models.PROTECT,
        related_name="budget_allocations",
    )
    subsector = models.ForeignKey(
        SubSector,
        on_delete=models.PROTECT,
        related_name="budget_allocations",
    )
    budget_type = models.CharField(max_length=12, choices=BudgetType.choices)
    allocated_amount = models.DecimalField(max_digits=18, decimal_places=2)
    spent_amount = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    data_classification = models.CharField(
        max_length=40,
        choices=DataClassification.choices,
        default=DataClassification.SYNTHETIC_DEMO,
    )
    source_url = models.URLField(blank=True)

    class Meta:
        ordering = ["local_government__name_en", "-fiscal_year__code", "subsector__name_en"]
        constraints = [
            models.UniqueConstraint(
                fields=["local_government", "fiscal_year", "subsector", "budget_type"],
                name="unique_local_fy_subsector_budget_type",
            ),
            models.CheckConstraint(
                condition=models.Q(allocated_amount__gte=0),
                name="allocation_amount_nonnegative",
            ),
            models.CheckConstraint(
                condition=models.Q(spent_amount__isnull=True) | models.Q(spent_amount__gte=0),
                name="allocation_spent_nonnegative_or_unknown",
            ),
        ]
        indexes = [
            models.Index(fields=["local_government", "fiscal_year", "budget_type"]),
        ]

    def __str__(self):
        return f"{self.local_government} · {self.fiscal_year} · {self.subsector}"
