from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("budgets", "0002_budgetallocation_evidence_review"),
    ]

    operations = [
        migrations.AlterField(
            model_name="budgetallocation",
            name="source_url",
            field=models.URLField(blank=True, max_length=1000),
        ),
    ]
