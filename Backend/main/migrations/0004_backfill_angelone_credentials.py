from django.db import migrations


def backfill_angelone_credentials(apps, schema_editor):
    from main.angelone.utils.crypto import encrypt_value

    ClientBrokerdetails = apps.get_model("main", "ClientBrokerdetails")

    for broker_detail in ClientBrokerdetails.objects.select_related("broker_name").all():
        broker_name = ""
        if getattr(broker_detail, "broker_name", None) and getattr(broker_detail.broker_name, "broker_name", None):
            broker_name = broker_detail.broker_name.broker_name.lower()
        if broker_name != "angel one":
            continue

        changed_fields = []

        raw_password = (broker_detail.broker_pass or "").strip()
        raw_totp_secret = (broker_detail.broker_Totp_Authcode or "").strip()

        if raw_password and not broker_detail.encrypted_broker_password:
            broker_detail.encrypted_broker_password = encrypt_value(raw_password)
            changed_fields.append("encrypted_broker_password")
        if broker_detail.broker_pass != (raw_password or None):
            broker_detail.broker_pass = raw_password or None
            changed_fields.append("broker_pass")
        if raw_password:
            broker_detail.broker_pass = None
            if "broker_pass" not in changed_fields:
                changed_fields.append("broker_pass")

        if raw_totp_secret and not broker_detail.encrypted_broker_totp_secret:
            broker_detail.encrypted_broker_totp_secret = encrypt_value(raw_totp_secret)
            changed_fields.append("encrypted_broker_totp_secret")
        if broker_detail.broker_Totp_Authcode != (raw_totp_secret or None):
            broker_detail.broker_Totp_Authcode = raw_totp_secret or None
            changed_fields.append("broker_Totp_Authcode")
        if raw_totp_secret:
            broker_detail.broker_Totp_Authcode = None
            if "broker_Totp_Authcode" not in changed_fields:
                changed_fields.append("broker_Totp_Authcode")

        if changed_fields:
            broker_detail.save(update_fields=changed_fields)


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0003_add_missing_clientbrokerdetails_fields"),
    ]

    operations = [
        migrations.RunPython(backfill_angelone_credentials, migrations.RunPython.noop),
    ]
