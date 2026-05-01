from django.db import migrations


DEFAULT_BROKERS = [
    {
        "broker_name": "Angel One",
        "description": "Store Angel One credentials securely, then use the daily broker login flow to create a trading session.",
    },
    {
        "broker_name": "Upstox",
        "description": "Save the Upstox API credentials, then use the broker redirect flow to connect the account.",
    },
    {
        "broker_name": "Zerodha",
        "description": "Save Zerodha API credentials, then complete the broker-side login flow from the trading panel.",
    },
    {
        "broker_name": "Alice Blue",
        "description": "Store Alice Blue identifiers used by the platform. Daily broker login is handled outside AlgoView.",
    },
    {
        "broker_name": "5Paisa",
        "description": "Save the 5Paisa API credentials used for daily login/session generation.",
    },
    {
        "broker_name": "FYERS",
        "description": "Save FYERS API credentials, then complete the broker login flow from the trading panel.",
    },
    {
        "broker_name": "Dhan",
        "description": "Store Dhan API key and access token. No extra broker redirect is required from this setup screen.",
    },
]


def seed_default_brokers(apps, schema_editor):
    Broker = apps.get_model("main", "Broker")

    for broker in DEFAULT_BROKERS:
        Broker.objects.get_or_create(
            broker_name=broker["broker_name"],
            defaults={
                "description": broker["description"],
                "is_active": True,
            },
        )


def noop(apps, schema_editor):
    return


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0007_seed_default_roles"),
    ]

    operations = [
        migrations.RunPython(seed_default_brokers, noop),
    ]
