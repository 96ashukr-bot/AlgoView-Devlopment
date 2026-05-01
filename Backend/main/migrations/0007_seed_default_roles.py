from django.db import migrations


def seed_default_roles(apps, schema_editor):
    Role = apps.get_model("main", "Role")

    def ensure_role(name):
        role = Role.objects.filter(name__iexact=name).first()
        if role:
            if getattr(role, "status", None) != "active":
                role.status = "active"
                role.save(update_fields=["status"])
            return role
        return Role.objects.create(name=name, status="active")

    ensure_role("Super-Admin")
    ensure_role("Sub-Admin")
    ensure_role("Client")


def noop_reverse(apps, schema_editor):
    return None


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0006_normalize_angel_one_broker_name"),
    ]

    operations = [
        migrations.RunPython(seed_default_roles, noop_reverse),
    ]
