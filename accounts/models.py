import re

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import secrets

from .managers import CustomUserManager


def validate_national_id(value: str):
    """
    اعتبارسنجی کد ملی ایران (۱۰ رقمی).
    - باید دقیقاً ۱۰ رقم باشد
    - چک‌سام استاندارد کد ملی ایران
    """
    if not value:
        return  # خالی بودن قبول است (null=True, blank=True)

    # فقط ۱۰ رقم مجاز
    if not re.match(r"^\d{10}$", value):
        raise ValidationError("کد ملی باید دقیقاً ۱۰ رقم باشد.")

    # چک‌سام کد ملی ایران
    check = int(value[9])
    s = sum(int(value[i]) * (10 - i) for i in range(9))
    remainder = s % 11

    valid = False
    if remainder < 2:
        valid = (check == remainder)
    else:
        valid = (check == (11 - remainder))

    if not valid:
        raise ValidationError("کد ملی نامعتبر است.")


class User(AbstractBaseUser, PermissionsMixin):
    phone_number = models.CharField(max_length=15, unique=True)
    full_name    = models.CharField(max_length=128, blank=True, default="")
    email        = models.EmailField(blank=True, null=True, unique=True)
    national_id  = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        unique=True,
        validators=[validate_national_id],
    )
    is_active    = models.BooleanField(default=True)
    is_staff     = models.BooleanField(default=False)
    date_joined  = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD  = "phone_number"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name        = "کاربر"
        verbose_name_plural = "کاربران"

    def __str__(self):
        return self.phone_number

    def clean(self):
        super().clean()
        if self.national_id:
            validate_national_id(self.national_id)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Address(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    title       = models.CharField(max_length=64, blank=True, default="")
    province    = models.CharField(max_length=64)
    city        = models.CharField(max_length=64)
    street      = models.TextField()
    postal_code = models.CharField(max_length=20)
    is_default  = models.BooleanField(default=False)

    class Meta:
        verbose_name        = "آدرس"
        verbose_name_plural = "آدرس‌ها"

    def __str__(self):
        return f"{self.user.phone_number} — {self.city}"


class OTPRecord(models.Model):
    phone_number = models.CharField(max_length=15, unique=True)
    code         = models.CharField(max_length=6)
    created_at   = models.DateTimeField(auto_now_add=True)
    expires_at   = models.DateTimeField()
    is_used      = models.BooleanField(default=False)
    last_sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "کد OTP"
        verbose_name_plural = "کدهای OTP"

    def __str__(self):
        return f"{self.phone_number} — {self.code}"

    def generate_code(self):
        from django.conf import settings
        expiry_minutes = getattr(settings, "OTP_EXPIRY_MINUTES", 2)
        self.code       = str(secrets.randbelow(900000) + 100000)
        self.expires_at = timezone.now() + timezone.timedelta(minutes=expiry_minutes)
        self.last_sent_at = timezone.now()
        self.is_used    = False
        self.save(update_fields=["code", "expires_at", "last_sent_at", "is_used"])

    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at
