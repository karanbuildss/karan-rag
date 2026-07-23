from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("procurement", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="tender",
            name="bid_security_amount",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=18,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="tender",
            name="bid_submission_deadline",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="tender",
            name="data_note_en",
            field=models.CharField(blank=True, max_length=300),
        ),
        migrations.AddField(
            model_name="tender",
            name="data_note_np",
            field=models.CharField(blank=True, max_length=300),
        ),
        migrations.AddField(
            model_name="tender",
            name="invitation_number",
            field=models.CharField(blank=True, db_index=True, max_length=80),
        ),
        migrations.AddConstraint(
            model_name="tender",
            constraint=models.CheckConstraint(
                condition=models.Q(bid_security_amount__isnull=True)
                | models.Q(bid_security_amount__gte=0),
                name="tender_bid_security_nonnegative_or_unknown",
            ),
        ),
    ]
