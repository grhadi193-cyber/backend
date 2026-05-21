# فاز ۴B — رفع sku null + تغییر on_delete به PROTECT برای category
from django.db import migrations, models


def fill_empty_sku(apps, schema_editor):
    """
    هر محصول با sku=NULL یا sku=\'\' را با مقدار یکتا پر می\u200cکند.
    فرمت: AUTO-<pk>  —  تضمین یکتایی و بدون تداخل با SKUهای واقعی.
    """
    Product = apps.get_model("store", "Product")
    for product in Product.objects.filter(
        models.Q(sku__isnull=True) | models.Q(sku="")
    ):
        product.sku = f"AUTO-{product.pk}"
        product.save(update_fields=["sku"])


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0009_order_idempotency_key"),
    ]

    operations = [
        # ── مرحله ۱: پر کردن یکتای NULLها قبل از AlterField ──────────────
        migrations.RunPython(fill_empty_sku, reverse_code=migrations.RunPython.noop),

        # ── مرحله ۲: تغییر فیلد sku (حذف null=True، اضافه default="") ──────
        migrations.AlterField(
            model_name="product",
            name="sku",
            field=models.CharField(
                blank=True,
                default="",
                max_length=100,
                unique=True,
            ),
        ),

        # ── مرحله ۳: تغییر on_delete از SET_NULL به PROTECT برای category ──
        migrations.AlterField(
            model_name="product",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.PROTECT,
                related_name="products",
                to="store.category",
            ),
        ),
    ]
