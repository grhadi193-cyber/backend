# Create default notification channels

from django.db import migrations


def create_default_channels(apps, schema_editor):
    NotificationChannel = apps.get_model("notifications", "NotificationChannel")

    defaults = [
        {"name": "sms", "is_active": True, "config": {}},
        {"name": "email", "is_active": False, "config": {}},
        {"name": "whatsapp", "is_active": False, "config": {}},
        {"name": "push", "is_active": False, "config": {}},
    ]

    for data in defaults:
        NotificationChannel.objects.get_or_create(name=data["name"], defaults=data)


def reverse_channels(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_default_channels, reverse_channels),
    ]
