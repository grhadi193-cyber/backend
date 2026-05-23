# Add Province, City, ShippingRate models

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("shipping", "0002_shippingzone_shippingmethod_cost_per_kg_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Province",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=64, unique=True, verbose_name="نام استان")),
                ("code", models.CharField(blank=True, max_length=10, verbose_name="کد استان")),
                ("is_active", models.BooleanField(default=True, verbose_name="فعال")),
            ],
            options={
                "verbose_name": "استان",
                "verbose_name_plural": "استان‌ها",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="City",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=64, verbose_name="نام شهر")),
                ("code", models.CharField(blank=True, max_length=10, verbose_name="کد شهر")),
                ("is_active", models.BooleanField(default=True, verbose_name="فعال")),
                (
                    "province",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cities",
                        to="shipping.province",
                        verbose_name="استان",
                    ),
                ),
            ],
            options={
                "verbose_name": "شهر",
                "verbose_name_plural": "شهرها",
                "ordering": ["name"],
                "unique_together": {("province", "name")},
            },
        ),
        migrations.AddField(
            model_name="shippingmethod",
            name="carrier_name",
            field=models.CharField(blank=True, default="", max_length=100, verbose_name="نام پستی/پیک"),
        ),
        migrations.AddField(
            model_name="shippingmethod",
            name="tracking_url_template",
            field=models.CharField(
                blank=True,
                default="",
                help_text="مثال: https://tracking.post.ir/?code={tracking_code}",
                max_length=500,
                verbose_name="قالب لینک رهگیری",
            ),
        ),
        migrations.CreateModel(
            name="ShippingRate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("weight_min", models.DecimalField(decimal_places=3, default=0, max_digits=8, verbose_name="حداقل وزن (kg)")),
                ("weight_max", models.DecimalField(decimal_places=3, default=0, max_digits=8, verbose_name="حداکثر وزن (kg)")),
                ("cost", models.DecimalField(decimal_places=0, max_digits=12, verbose_name="هزینه")),
                ("is_active", models.BooleanField(default=True, verbose_name="فعال")),
                (
                    "city",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="shipping_rates",
                        to="shipping.city",
                        verbose_name="شهر",
                    ),
                ),
                (
                    "province",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="shipping_rates",
                        to="shipping.province",
                        verbose_name="استان",
                    ),
                ),
                (
                    "shipping_method",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rates",
                        to="shipping.shippingmethod",
                        verbose_name="روش ارسال",
                    ),
                ),
            ],
            options={
                "verbose_name": "تعرفه ارسال",
                "verbose_name_plural": "تعرفه‌های ارسال",
                "ordering": ["province", "city", "weight_min"],
                "unique_together": {("shipping_method", "province", "city", "weight_min")},
            },
        ),
    ]
