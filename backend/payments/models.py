from config.models import DataClassification
from django.db import models
from procurement.models import ContractAward
from projects.models import ProjectMilestone


class Payment(models.Model):
    contract_award = models.ForeignKey(
        ContractAward,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    milestone = models.ForeignKey(
        ProjectMilestone,
        on_delete=models.PROTECT,
        related_name="payments",
        null=True,
        blank=True,
    )
    reference = models.CharField(max_length=80, unique=True)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    paid_on = models.DateField()
    description_en = models.CharField(max_length=240, blank=True)
    description_np = models.CharField(max_length=240, blank=True)
    source_url = models.URLField(blank=True)
    data_classification = models.CharField(
        max_length=40,
        choices=DataClassification.choices,
        default=DataClassification.SYNTHETIC_DEMO,
    )

    class Meta:
        ordering = ["paid_on", "reference"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gte=0),
                name="payment_amount_nonnegative",
            )
        ]
        indexes = [models.Index(fields=["contract_award", "paid_on"])]

    def __str__(self):
        return self.reference
