from django.db import migrations


def normalize_angel_one_broker_name(apps, schema_editor):
    Broker = apps.get_model("main", "Broker")
    for broker_name in ["Angle One", "angle one", "ANGLE ONE", "AngelOne", "angleone"]:
        Broker.objects.filter(broker_name=broker_name).update(broker_name="Angel One")


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0005_clientbrokerdetails_broker_last_logout_at"),
    ]

    operations = [
        migrations.RunPython(normalize_angel_one_broker_name, noop_reverse),
    ]
