from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("main", "0028_daily_trade_limit_counters"),
    ]

    operations = [
        migrations.CreateModel(
            name="AwsAmiNodeClaim",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_ip", models.GenericIPAddressField(unique=True)),
                ("node_name", models.CharField(max_length=150)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("activated", "Activated"), ("expired", "Expired"), ("cancelled", "Cancelled")], db_index=True, default="pending", max_length=20)),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("activated_at", models.DateTimeField(blank=True, null=True)),
                ("agent_version", models.CharField(blank=True, max_length=50, null=True)),
                ("instance_id", models.CharField(blank=True, max_length=100, null=True, unique=True)),
                ("ami_id", models.CharField(blank=True, max_length=100, null=True)),
                ("region", models.CharField(blank=True, max_length=50, null=True)),
                ("architecture", models.CharField(blank=True, max_length=30, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("client", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="aws_ami_node_claim", to=settings.AUTH_USER_MODEL)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_aws_ami_node_claims", to=settings.AUTH_USER_MODEL)),
                ("execution_node", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="aws_ami_claim", to="main.executionnode")),
            ],
        ),
        migrations.AddIndex(
            model_name="awsaminodeclaim",
            index=models.Index(fields=["public_ip", "status"], name="main_awsami_public__2cbca1_idx"),
        ),
        migrations.AddIndex(
            model_name="awsaminodeclaim",
            index=models.Index(fields=["client", "status"], name="main_awsami_client__3aa22e_idx"),
        ),
    ]
