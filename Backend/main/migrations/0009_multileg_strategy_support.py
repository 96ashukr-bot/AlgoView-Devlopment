from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0008_seed_default_brokers"),
    ]

    operations = [
        migrations.AddField(
            model_name="strategies",
            name="execution_mode",
            field=models.CharField(
                choices=[
                    ("INDICATOR_BASED", "Indicator Based Strategies"),
                    ("MULTI_LEG", "Multi Leg Option Strategies"),
                ],
                default="INDICATOR_BASED",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="strategies",
            name="multi_leg_template",
            field=models.CharField(
                blank=True,
                choices=[
                    ("SHORT_STRADDLE", "Short Straddle"),
                    ("BULL_CALL_SPREAD", "Bull Call Spread"),
                    ("BEAR_PUT_SPREAD", "Bear Put Spread"),
                    ("LONG_CALL_BUTTERFLY", "Long Call Butterfly"),
                    ("SHORT_CALL_BUTTERFLY", "Short Call Butterfly"),
                    ("LONG_CALL_CONDOR", "Long Call Condor"),
                    ("SHORT_CALL_CONDOR", "Short Call Condor"),
                    ("LONG_IRON_CONDOR", "Long Iron Condor"),
                    ("SHORT_IRON_BUTTERFLY", "Short Iron Butterfly"),
                ],
                max_length=40,
                null=True,
            ),
        ),
        migrations.CreateModel(
            name="ClientMultiLegStrategySetting",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("group_service", models.CharField(blank=True, max_length=255, null=True)),
                ("broker", models.CharField(blank=True, max_length=50, null=True)),
                ("product_type", models.CharField(blank=True, max_length=20, null=True)),
                ("order_type", models.CharField(blank=True, choices=[("MARKET", "MARKET"), ("LIMIT", "LIMIT")], default="LIMIT", max_length=20, null=True)),
                ("buffer_percentage", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ("quantity", models.IntegerField(blank=True, null=True)),
                ("trade_limit", models.IntegerField(blank=True, null=True)),
                ("max_loss_for_day", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("max_profit_for_day", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("expiry_date", models.DateTimeField(blank=True, null=True)),
                ("is_tread_status", models.BooleanField(default=False)),
                ("sl_type", models.CharField(blank=True, max_length=50, null=True)),
                ("stop_loss", models.IntegerField(blank=True, null=True)),
                ("target", models.IntegerField(blank=True, null=True)),
                ("legs", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="multi_leg_trade_settings", to="main.user")),
                ("segment", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="main.segment")),
                ("strategy", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="client_multi_leg_settings", to="main.strategies")),
            ],
            options={
                "unique_together": {("client", "strategy")},
            },
        ),
    ]
