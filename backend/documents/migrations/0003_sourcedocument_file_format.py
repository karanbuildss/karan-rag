from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("documents", "0002_alter_projectdocumentlink_relationship")]

    operations = [
        migrations.AlterField(
            model_name="sourcedocument",
            name="document_type",
            field=models.CharField(
                choices=[
                    ("budget_book", "Budget book / red book"),
                    ("budget_speech", "Budget speech"),
                    ("annual_program", "Annual policy or program"),
                    ("economic_act", "Economic act or bill"),
                    ("progress_report", "Progress report"),
                    ("expenditure_report", "Expenditure report"),
                    ("procurement_notice", "Procurement notice"),
                    ("contract_award", "Contract award"),
                    ("payment_record", "Payment record"),
                    ("audit_report", "Audit report"),
                    ("other", "Other"),
                ],
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="sourcedocument",
            name="file_format",
            field=models.CharField(
                choices=[("pdf", "PDF"), ("image", "Image")],
                default="pdf",
                max_length=10,
            ),
        )
    ]
