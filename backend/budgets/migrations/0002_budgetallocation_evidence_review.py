import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("budgets", "0001_initial"),
        ("documents", "0002_alter_projectdocumentlink_relationship"),
    ]

    operations = [
        migrations.AlterField(
            model_name="budgetallocation",
            name="budget_type",
            field=models.CharField(
                choices=[
                    ("recurrent", "Recurrent"),
                    ("capital", "Capital"),
                    ("financing", "Financing"),
                    ("total", "Reported total"),
                ],
                max_length=12,
            ),
        ),
        migrations.AddField(
            model_name="budgetallocation",
            name="source_document",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="budget_allocations",
                to="documents.sourcedocument",
            ),
        ),
        migrations.AddField(
            model_name="budgetallocation",
            name="source_page",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="budgetallocation",
            name="review_status",
            field=models.CharField(
                choices=[
                    ("review_required", "Review required"),
                    ("reviewed", "Reviewed"),
                ],
                default="review_required",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="budgetallocation",
            name="reliability",
            field=models.CharField(
                choices=[
                    ("limited", "Limited"),
                    ("moderate", "Moderate"),
                    ("strong", "Strong"),
                ],
                default="limited",
                max_length=12,
            ),
        ),
        migrations.AddField(
            model_name="budgetallocation",
            name="comparability",
            field=models.CharField(
                choices=[
                    ("not_comparable", "Not comparable"),
                    ("limited", "Limited comparability"),
                    ("strong", "Strong comparability"),
                ],
                default="limited",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="budgetallocation",
            name="source_scope_en",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="budgetallocation",
            name="source_scope_np",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddConstraint(
            model_name="budgetallocation",
            constraint=models.CheckConstraint(
                condition=models.Q(source_page__isnull=True)
                | models.Q(source_page__gte=1),
                name="allocation_source_page_positive",
            ),
        ),
    ]
