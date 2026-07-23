from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("projects", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="status",
            field=models.CharField(
                choices=[
                    ("unknown", "Unknown / not evidenced"),
                    ("planned", "Planned"),
                    ("procurement", "Procurement"),
                    ("implementation", "Implementation"),
                    ("delayed", "Delayed"),
                    ("completed", "Completed"),
                    ("on_hold", "On hold"),
                ],
                max_length=20,
            ),
        )
    ]
