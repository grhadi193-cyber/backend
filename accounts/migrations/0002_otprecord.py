from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="OTPRecord",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("phone_number", models.CharField(db_index=True, max_length=15)),
                ("code", models.CharField(max_length=6)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("is_used", models.BooleanField(default=False)),
            ],
            options={
                "verbose_name": "\u06a9\u062f OTP",
                "verbose_name_plural": "\u06a9\u062f\u0647\u0627\u06cc OTP",
                "ordering": ["-created_at"],
            },
        ),
    ]
