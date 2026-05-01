from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0002_secure_angelone_broker_storage"),
    ]

    operations = [
        migrations.AddField(
            model_name="clientbrokerdetails",
            name="buffer_percentage",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                default=2.50,
                help_text="Buffer percentage for limit orders (0.1 to 10.0). Default: 2.5%",
                max_digits=5,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="clientbrokerdetails",
            name="enable_market_orders",
            field=models.BooleanField(
                default=False,
                help_text="Market orders are disabled by default for compliance",
            ),
        ),
    ]
