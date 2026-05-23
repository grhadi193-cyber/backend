from typing import Optional

from django.conf import settings
from django.utils import timezone
from django.contrib.auth.hashers import check_password, make_password

from core.exceptions import AppException
from sms.services import send_otp as send_otp_code

from .models import User, Address, OTPRecord


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def _hash_password(raw: str) -> str:
    return make_password(raw)


def _check_password(user: User, raw: str) -> bool:
    return check_password(raw, user.password)


def _user_has_password(user: User) -> bool:
    """Return True if the user has a usable (hashed) password."""
    return user.has_usable_password()


def send_otp(phone_number: str) -> None:
    record, created = OTPRecord.objects.get_or_create(
        phone_number=phone_number,
        defaults={"code": "000000", "expires_at": timezone.now()},
    )

    if not created:
        rate_limit = getattr(settings, "OTP_RATE_LIMIT_SECONDS", 60)
        time_since_last = (timezone.now() - record.last_sent_at).total_seconds()
        if time_since_last < rate_limit:
            remaining = int(rate_limit - time_since_last)
            raise AppException(
                f"لطفاً {remaining} ثانیه دیگر تلاش کنید.",
                status_code=429,
            )

    record.generate_code()
    send_otp_code(phone_number, record.code)


def verify_otp(phone_number: str, code: str, password: Optional[str] = None) -> User:
    try:
        record = OTPRecord.objects.get(phone_number=phone_number, is_used=False)
    except OTPRecord.DoesNotExist:
        raise AppException("کد تایید یافت نشد", status_code=400)

    if record.is_expired():
        raise AppException("کد تایید منقضی شده است", status_code=400)

    if record.code != code:
        raise AppException("کد تایید اشتباه است", status_code=400)

    record.is_used = True
    record.save(update_fields=["is_used"])

    user, created = User.objects.get_or_create(phone_number=phone_number)
    user.is_active = True

    # If a password is provided, set it (registration / password reset flow)
    if password:
        user.set_password(password)
        user.save(update_fields=["is_active", "password"])
    else:
        user.save(update_fields=["is_active"])

    return user


def login_with_password(phone_number: str, password: str) -> User:
    """Authenticate a user with phone number + password."""
    try:
        user = User.objects.get(phone_number=phone_number)
    except User.DoesNotExist:
        raise AppException("کاربری با این شماره موبایل یافت نشد", status_code=404)

    if not user.is_active:
        raise AppException("حساب کاربری غیرفعال است", status_code=403)

    if not _user_has_password(user):
        raise AppException("برای این حساب رمز عبور تعریف نشده است. لطفاً با OTP وارد شوید", status_code=400)

    if not _check_password(user, password):
        raise AppException("شماره موبایل یا رمز عبور اشتباه است", status_code=401)

    return user


def forgot_password(phone_number: str) -> None:
    """Send an OTP for password reset. Raises if user does not exist."""
    if not User.objects.filter(phone_number=phone_number).exists():
        raise AppException("کاربری با این شماره موبایل یافت نشد", status_code=404)
    send_otp(phone_number)


def reset_password(phone_number: str, code: str, new_password: str) -> User:
    """Verify OTP and set a new password."""
    user = verify_otp(phone_number, code, password=new_password)
    return user


def change_password(user: User, old_password: str, new_password: str) -> None:
    """Change password for an authenticated user."""
    if not _check_password(user, old_password):
        raise AppException("رمز عبور فعلی اشتباه است", status_code=400)
    user.set_password(new_password)
    user.save(update_fields=["password"])


def get_addresses(user: User) -> list:
    return list(user.addresses.all())


def create_address(
    user: User,
    title: str,
    province: str,
    city: str,
    street: str,
    postal_code: str,
    is_default: bool,
) -> Address:
    if is_default:
        user.addresses.filter(is_default=True).update(is_default=False)
    return Address.objects.create(
        user=user,
        title=title,
        province=province,
        city=city,
        street=street,
        postal_code=postal_code,
        is_default=is_default,
    )


def delete_address(user: User, address_id: int) -> None:
    try:
        address = user.addresses.get(pk=address_id)
    except Address.DoesNotExist:
        raise AppException("آدرس یافت نشد", status_code=404)
    address.delete()


def get_profile(user: User) -> User:
    return user


def update_profile(
    user: User,
    full_name: Optional[str],
    email: Optional[str],
    national_id: Optional[str],
) -> User:
    updated_fields: list[str] = []

    if full_name is not None:
        user.full_name = full_name.strip()
        updated_fields.append("full_name")

    if email is not None:
        user.email = email.strip() or None
        updated_fields.append("email")

    if national_id is not None:
        nid = national_id.strip() or None
        if nid is not None:
            # بررسی unique بودن — کاربر دیگری همین کد ملی را ندارد
            if (
                User.objects.filter(national_id=nid)
                .exclude(pk=user.pk)
                .exists()
            ):
                raise AppException("کد ملی تکراری است", status_code=400)
        user.national_id = nid
        updated_fields.append("national_id")

    if updated_fields:
        user.save(update_fields=updated_fields)

    return user
