from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0019_chatthread_chatmessage_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="tradeorderhistory",
            name="trade_setting",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="order_histories",
                to="main.clienttradesetting",
            ),
        ),
        migrations.AddField(
            model_name="tradeorderhistory",
            name="sltp_metadata",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="tradeorderhistory",
            name="sltp_status",
            field=models.CharField(blank=True, db_index=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="tradeorderhistory",
            name="sltp_last_action",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="tradeorderhistory",
            name="sltp_last_failure_reason",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="tradeorderhistory",
            name="sltp_retry_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="tradeorderhistory",
            name="sltp_manual_attention",
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name="tradeorderhistory",
            name="sltp_last_checked_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
