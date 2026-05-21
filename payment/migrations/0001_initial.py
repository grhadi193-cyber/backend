from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("store", "0003_rename_total_amount_total_price"),
    ]

    operations = [
        migrations.CreateModel(
            name="Transaction",
            fields=[
                ("id",               models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount",           models.DecimalField(decimal_places=0, max_digits=14)),
                ("ref_id",           models.CharField(blank=True, default="", max_length=128)),
                ("status",           models.CharField(
                    choices=[("pending", "Pending"), ("success", "Success"), ("failed", "Failed")],
                    default="pending",
                    max_length=16,
                )),
                ("gateway_response", models.JSONField(blank=True, default=dict)),
                ("created_at",       models.DateTimeField(auto_now_add=True)),
                ("order",            models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="transactions",
                    to="store.order",
                )),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
