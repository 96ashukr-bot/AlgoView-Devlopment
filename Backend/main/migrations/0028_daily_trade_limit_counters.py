from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("main", "0027_subadmindashboardannouncement_media"),
    ]

    operations = [
        migrations.CreateModel(
            name="DailyTradeLimitCounter",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("trade_date", models.DateField(db_index=True)),
                ("symbol", models.CharField(max_length=50)),
                ("successful_buy_count", models.PositiveIntegerField(default=0)),
                ("initialized_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="daily_trade_limit_counters", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="DailyTradeLimitReservation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("request_id", models.CharField(max_length=128)),
                ("status", models.CharField(choices=[("RESERVED", "Reserved"), ("SUCCESS", "Successful BUY"), ("RELEASED", "Released")], default="RESERVED", max_length=12)),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("counter", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reservations", to="main.dailytradelimitcounter")),
            ],
        ),
        migrations.AddConstraint(
            model_name="dailytradelimitcounter",
            constraint=models.UniqueConstraint(fields=("client", "trade_date", "symbol"), name="unique_daily_trade_limit_counter"),
        ),
        migrations.AddIndex(
            model_name="dailytradelimitcounter",
            index=models.Index(fields=["client", "trade_date", "symbol"], name="trade_limit_counter_lookup"),
        ),
        migrations.AddConstraint(
            model_name="dailytradelimitreservation",
            constraint=models.UniqueConstraint(fields=("counter", "request_id"), name="unique_daily_trade_limit_reservation"),
        ),
        migrations.AddIndex(
            model_name="dailytradelimitreservation",
            index=models.Index(fields=["counter", "status", "expires_at"], name="trade_limit_reservation_lookup"),
        ),
    ]
