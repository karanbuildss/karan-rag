from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("documents", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="projectdocumentlink",
            name="relationship",
            field=models.CharField(
                choices=[
                    ("context", "Municipal context"),
                    ("allocation", "Budget allocation"),
                    ("audit", "Official audit finding"),
                    ("procurement", "Procurement"),
                    ("payment", "Payment"),
                    ("progress", "Progress"),
                    ("completion", "Completion"),
                ],
                max_length=20,
            ),
        )
    ]
