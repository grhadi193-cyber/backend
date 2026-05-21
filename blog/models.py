from django.db import models


class Post(models.Model):
    title = models.CharField(max_length=255, verbose_name="عنوان")
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True, verbose_name="اسلاگ")
    content = models.TextField(verbose_name="محتوا")
    featured_image = models.ImageField(
        upload_to="blog/images/",
        null=True,
        blank=True,
        verbose_name="تصویر شاخص",
    )
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ انتشار")
    is_published = models.BooleanField(default=False, verbose_name="منتشر شده")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        ordering = ["-published_at"]
        verbose_name = "پست"
        verbose_name_plural = "پست‌ها"

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        from django.utils import timezone
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
