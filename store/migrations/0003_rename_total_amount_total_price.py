from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0002_order_alter_category_options_alter_product_options_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="order",
            old_name="total_amount",
            new_name="total_price",
        ),
    ]
