from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0004_backfill_angelone_credentials"),
    ]

    operations = [
        migrations.AddField(
            model_name="clientbrokerdetails",
            name="broker_last_logout_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
