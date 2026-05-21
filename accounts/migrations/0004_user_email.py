from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_alter_address_options_alter_user_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="email",
            field=models.EmailField(blank=True, default="", max_length=254),
        ),
    ]
