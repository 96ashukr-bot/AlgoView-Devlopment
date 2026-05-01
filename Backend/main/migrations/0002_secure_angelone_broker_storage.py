from django.db import migrations, models


def migrate_angelone_sensitive_fields(apps, schema_editor):
    from main.angelone.utils.crypto import encrypt_value

    ClientBrokerdetails = apps.get_model("main", "ClientBrokerdetails")

    for broker_detail in ClientBrokerdetails.objects.select_related("broker_name").all():
        broker_name = ""
        if getattr(broker_detail, "broker_name", None) and getattr(broker_detail.broker_name, "broker_name", None):
            broker_name = broker_detail.broker_name.broker_name.lower()
        if broker_name != "angel one":
            continue

        changed_fields = []

        if broker_detail.broker_API_SKEY and not broker_detail.encrypted_broker_api_secret:
            broker_detail.encrypted_broker_api_secret = encrypt_value(broker_detail.broker_API_SKEY)
            broker_detail.broker_API_SKEY = None
            changed_fields.extend(["encrypted_broker_api_secret", "broker_API_SKEY"])

        if broker_detail.broker_pass and not broker_detail.encrypted_broker_password:
            broker_detail.encrypted_broker_password = encrypt_value(broker_detail.broker_pass)
            broker_detail.broker_pass = None
            changed_fields.extend(["encrypted_broker_password", "broker_pass"])

        if broker_detail.broker_Totp_Authcode and not broker_detail.encrypted_broker_totp_secret:
            broker_detail.encrypted_broker_totp_secret = encrypt_value(broker_detail.broker_Totp_Authcode)
            broker_detail.broker_Totp_Authcode = None
            changed_fields.extend(["encrypted_broker_totp_secret", "broker_Totp_Authcode"])

        if broker_detail.access_token and not broker_detail.encrypted_access_token:
            broker_detail.encrypted_access_token = encrypt_value(broker_detail.access_token)
            broker_detail.access_token = None
            changed_fields.extend(["encrypted_access_token", "access_token"])

        if broker_detail.refreshToken and not broker_detail.encrypted_refresh_token:
            broker_detail.encrypted_refresh_token = encrypt_value(broker_detail.refreshToken)
            broker_detail.refreshToken = None
            changed_fields.extend(["encrypted_refresh_token", "refreshToken"])

        if getattr(broker_detail, "feed_token", None) and not broker_detail.encrypted_feed_token:
            broker_detail.encrypted_feed_token = encrypt_value(broker_detail.feed_token)
            broker_detail.feed_token = None
            changed_fields.extend(["encrypted_feed_token", "feed_token"])

        if changed_fields:
            broker_detail.save(update_fields=changed_fields)


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0001_initial"),
        ("main", "0001_add_order_type_and_buffer_to_client_trade_setting"),
    ]

    operations = [
        migrations.AddField(
            model_name="clientbrokerdetails",
            name="encrypted_access_token",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="clientbrokerdetails",
            name="encrypted_broker_api_secret",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="clientbrokerdetails",
            name="encrypted_broker_password",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="clientbrokerdetails",
            name="encrypted_broker_totp_secret",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="clientbrokerdetails",
            name="encrypted_feed_token",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="clientbrokerdetails",
            name="encrypted_refresh_token",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="clientbrokerdetails",
            name="feed_token",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.RunPython(migrate_angelone_sensitive_fields, migrations.RunPython.noop),
    ]
