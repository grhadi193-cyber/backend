from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0004_alter_category_name_alter_category_slug_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="tracking_number",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="order",
            name="postal_tracking",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
    ]
