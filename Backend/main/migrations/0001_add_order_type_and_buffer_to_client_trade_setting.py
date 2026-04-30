from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="clienttradesetting",
            name="buffer_percentage",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name="clienttradesetting",
            name="order_type",
            field=models.CharField(
                blank=True,
                choices=[("MARKET", "MARKET"), ("LIMIT", "LIMIT")],
                default="LIMIT",
                max_length=20,
                null=True,
            ),
        ),
    ]
