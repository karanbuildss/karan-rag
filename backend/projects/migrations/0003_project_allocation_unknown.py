from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0002_alter_project_status"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="project",
            name="project_allocated_amount_nonnegative",
        ),
        migrations.AlterField(
            model_name="project",
            name="allocated_amount",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=18,
                null=True,
            ),
        ),
        migrations.AddConstraint(
            model_name="project",
            constraint=models.CheckConstraint(
                condition=models.Q(allocated_amount__isnull=True)
                | models.Q(allocated_amount__gte=0),
                name="project_allocated_amount_nonnegative_or_unknown",
            ),
        ),
    ]
