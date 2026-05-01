from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0009_multileg_strategy_support"),
    ]

    operations = [
        migrations.CreateModel(
            name="StrategyExecution",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("broker", models.CharField(max_length=100)),
                ("strategy_name", models.CharField(max_length=100)),
                ("underlying", models.CharField(max_length=100)),
                ("expiry", models.DateTimeField(blank=True, null=True)),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("EXECUTING", "Executing"), ("ACTIVE", "Active"), ("EXITING", "Exiting"), ("EXITED", "Exited"), ("FAILED", "Failed"), ("ROLLED_BACK", "Rolled Back"), ("CANCELLED", "Cancelled")], default="PENDING", max_length=20)),
                ("entry_time", models.DateTimeField(blank=True, null=True)),
                ("exit_time", models.DateTimeField(blank=True, null=True)),
                ("total_quantity", models.IntegerField(default=0)),
                ("combined_pnl", models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ("max_pnl_seen", models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ("trailing_stop_level", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ("exit_reason", models.CharField(blank=True, max_length=255, null=True)),
                ("idempotency_key", models.CharField(blank=True, max_length=150, null=True, unique=True)),
                ("config_snapshot", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="strategy_executions", to="main.user")),
            ],
        ),
        migrations.CreateModel(
            name="StrategyExecutionLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(max_length=100)),
                ("message", models.TextField()),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("strategy_execution", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="logs", to="main.strategyexecution")),
            ],
        ),
        migrations.CreateModel(
            name="StrategyLeg",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("leg_name", models.CharField(max_length=100)),
                ("transaction_type", models.CharField(choices=[("BUY", "BUY"), ("SELL", "SELL")], max_length=4)),
                ("option_type", models.CharField(choices=[("CE", "CE"), ("PE", "PE")], max_length=2)),
                ("strike_price", models.DecimalField(decimal_places=2, max_digits=12)),
                ("symbol", models.CharField(max_length=255)),
                ("token", models.CharField(blank=True, max_length=100, null=True)),
                ("lot_size", models.IntegerField(default=0)),
                ("quantity", models.IntegerField(default=0)),
                ("order_type", models.CharField(blank=True, max_length=20, null=True)),
                ("limit_price", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("broker_order_id", models.CharField(blank=True, max_length=255, null=True)),
                ("entry_price", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("exit_price", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("status", models.CharField(choices=[("PLANNED", "Planned"), ("EXECUTING", "Executing"), ("ACTIVE", "Active"), ("EXITING", "Exiting"), ("EXITED", "Exited"), ("FAILED", "Failed"), ("ROLLED_BACK", "Rolled Back")], default="PLANNED", max_length=20)),
                ("pnl", models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ("stop_loss", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("exchange", models.CharField(default="NFO", max_length=20)),
                ("order_response", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("strategy_execution", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="legs", to="main.strategyexecution")),
            ],
        ),
    ]
