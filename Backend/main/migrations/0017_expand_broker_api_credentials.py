from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0016_executionorderjob_main_execut_client__7173ce_idx_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="clientbrokerdetails",
            name="broker_API_KEY",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="clientbrokerdetails",
            name="broker_API_SKEY",
            field=models.TextField(blank=True, null=True),
        ),
    ]
