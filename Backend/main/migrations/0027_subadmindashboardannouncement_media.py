from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0026_execution_node_multi_client_assignments"),
    ]

    operations = [
        migrations.AddField(
            model_name="subadmindashboardannouncement",
            name="media",
            field=models.FileField(blank=True, null=True, upload_to="subadmin_announcements/"),
        ),
    ]
