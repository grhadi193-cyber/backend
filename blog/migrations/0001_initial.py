from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Post",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255, verbose_name="عنوان")),
                ("slug", models.SlugField(allow_unicode=True, max_length=255, unique=True, verbose_name="اسلاگ")),
                ("content", models.TextField(verbose_name="محتوا")),
                ("featured_image", models.ImageField(blank=True, null=True, upload_to="blog/images/", verbose_name="تصویر شاخص")),
                ("published_at", models.DateTimeField(blank=True, null=True, verbose_name="تاریخ انتشار")),
                ("is_published", models.BooleanField(default=False, verbose_name="منتشر شده")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")),
            ],
            options={
                "verbose_name": "پست",
                "verbose_name_plural": "پست‌ها",
                "ordering": ["-published_at"],
            },
        ),
    ]
