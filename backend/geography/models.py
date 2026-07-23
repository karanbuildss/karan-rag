from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Province(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name_en = models.CharField(max_length=100)
    name_np = models.CharField(max_length=100)

    class Meta:
        ordering = ["name_en"]

    def __str__(self):
        return self.name_en


class District(models.Model):
    code = models.CharField(max_length=10, unique=True)
    province = models.ForeignKey(Province, on_delete=models.PROTECT, related_name="districts")
    name_en = models.CharField(max_length=100)
    name_np = models.CharField(max_length=100)

    class Meta:
        ordering = ["name_en"]

    def __str__(self):
        return self.name_en


class LocalGovernment(models.Model):
    class GovernmentType(models.TextChoices):
        METROPOLITAN = "metropolitan", "Metropolitan city"
        SUB_METROPOLITAN = "sub_metropolitan", "Sub-metropolitan city"
        MUNICIPALITY = "municipality", "Municipality"
        RURAL_MUNICIPALITY = "rural_municipality", "Rural municipality"

    code = models.CharField(max_length=20, unique=True)
    district = models.ForeignKey(
        District,
        on_delete=models.PROTECT,
        related_name="local_governments",
    )
    name_en = models.CharField(max_length=150)
    name_np = models.CharField(max_length=150)
    government_type = models.CharField(max_length=24, choices=GovernmentType.choices)

    class Meta:
        ordering = ["name_en"]
        indexes = [models.Index(fields=["government_type", "name_en"])]

    def __str__(self):
        return self.name_en


class Ward(models.Model):
    local_government = models.ForeignKey(
        LocalGovernment,
        on_delete=models.CASCADE,
        related_name="wards",
    )
    number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(99)]
    )
    name_en = models.CharField(max_length=100, blank=True)
    name_np = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["local_government__name_en", "number"]
        constraints = [
            models.UniqueConstraint(
                fields=["local_government", "number"],
                name="unique_ward_per_local_government",
            ),
            models.CheckConstraint(
                condition=models.Q(number__gte=1, number__lte=99),
                name="ward_number_between_1_and_99",
            ),
        ]

    def __str__(self):
        return f"{self.local_government} Ward {self.number}"
