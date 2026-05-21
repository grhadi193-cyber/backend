from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0008_product_discount_price_product_meta_description_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="idempotency_key",
            field=models.CharField(blank=True, db_index=True, max_length=64),
        ),
    ]
