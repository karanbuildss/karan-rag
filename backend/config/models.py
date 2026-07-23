from django.db import models


class DataClassification(models.TextChoices):
    OFFICIAL = "official", "Official"
    RECONSTRUCTED = "reconstructed_from_official_sources", "Reconstructed from official sources"
    CURATED_DEMO = "curated_demo", "Curated demo"
    SYNTHETIC_DEMO = "synthetic_demo", "Synthetic demo"
