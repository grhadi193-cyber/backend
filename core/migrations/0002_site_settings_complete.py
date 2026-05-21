from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="site_name",
            field=models.CharField(default="\u0641\u0631\u0648\u0634\u06af\u0627\u0647 \u0645\u0646", max_length=200),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="logo",
            field=models.ImageField(blank=True, null=True, upload_to="site/"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="banner_text",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="announcement",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="primary_color",
            field=models.CharField(default="#01696f", max_length=7),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="maintenance_mode",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="social_instagram",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="social_telegram",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="support_phone",
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
