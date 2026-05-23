from typing import List
from ninja import Router
from django.http import JsonResponse

from core.auth import AuthBearer
from core.exceptions import AppException
from .schemas import (
    SendOTPIn, VerifyOTPIn, TokenOut,
    LoginIn, ForgotPasswordIn, ResetPasswordIn, ChangePasswordIn,
    AddressIn, AddressOut,
    ProfileOut, UpdateProfileIn,
)
from . import services as svc

router = Router(tags=["Auth"])

_auth = AuthBearer()


@router.post("/send-otp", auth=None, summary="ارسال کد OTP")
def send_otp(request, payload: SendOTPIn):
    try:
        svc.send_otp(payload.phone_number)
    except AppException as e:
        return JsonResponse(
            {"error": True, "code": "otp_error", "message": e.detail},
            status=e.status_code,
        )
    return {"detail": "کد تایید ارسال شد"}


@router.post("/verify-otp", auth=None, response=TokenOut, summary="تایید OTP و دریافت توکن")
def verify_otp(request, payload: VerifyOTPIn):
    from rest_framework_simplejwt.tokens import RefreshToken
    try:
        user = svc.verify_otp(payload.phone_number, payload.code, password=payload.password)
    except AppException as e:
        return JsonResponse(
            {"error": True, "code": "otp_invalid", "message": e.detail},
            status=e.status_code,
        )
    refresh = RefreshToken.for_user(user)
    return TokenOut(access=str(refresh.access_token), refresh=str(refresh))


@router.post("/login", auth=None, response=TokenOut, summary="ورود با رمز عبور")
def login(request, payload: LoginIn):
    from rest_framework_simplejwt.tokens import RefreshToken
    try:
        user = svc.login_with_password(payload.phone_number, payload.password)
    except AppException as e:
        return JsonResponse(
            {"error": True, "code": "login_error", "message": e.detail},
            status=e.status_code,
        )
    refresh = RefreshToken.for_user(user)
    return TokenOut(access=str(refresh.access_token), refresh=str(refresh))


@router.post("/forgot-password", auth=None, summary="درخواست بازنشانی رمز عبور (ارسال OTP)")
def forgot_password(request, payload: ForgotPasswordIn):
    try:
        svc.forgot_password(payload.phone_number)
    except AppException as e:
        return JsonResponse(
            {"error": True, "code": "forgot_password_error", "message": e.detail},
            status=e.status_code,
        )
    return {"detail": "کد تایید برای بازنشانی رمز عبور ارسال شد"}


@router.post("/reset-password", auth=None, response=TokenOut, summary="بازنشانی رمز عبور با OTP")
def reset_password(request, payload: ResetPasswordIn):
    from rest_framework_simplejwt.tokens import RefreshToken
    try:
        user = svc.reset_password(payload.phone_number, payload.code, payload.new_password)
    except AppException as e:
        return JsonResponse(
            {"error": True, "code": "reset_password_error", "message": e.detail},
            status=e.status_code,
        )
    refresh = RefreshToken.for_user(user)
    return TokenOut(access=str(refresh.access_token), refresh=str(refresh))


@router.post("/change-password", auth=_auth, summary="تغییر رمز عبور")
def change_password(request, payload: ChangePasswordIn):
    try:
        svc.change_password(request.auth, payload.old_password, payload.new_password)
    except AppException as e:
        return JsonResponse(
            {"error": True, "code": "change_password_error", "message": e.detail},
            status=e.status_code,
        )
    return {"detail": "رمز عبور با موفقیت تغییر یافت"}


@router.get("/addresses", auth=_auth, response=List[AddressOut], summary="لیست آدرس‌ها")
def list_addresses(request):
    return svc.get_addresses(request.auth)


@router.post("/addresses", auth=_auth, response=AddressOut, summary="افزودن آدرس")
def create_address(request, payload: AddressIn):
    return svc.create_address(
        request.auth,
        payload.title,
        payload.province,
        payload.city,
        payload.street,
        payload.postal_code,
        payload.is_default,
    )


@router.delete("/addresses/{address_id}", auth=_auth, summary="حذف آدرس")
def delete_address(request, address_id: int):
    try:
        svc.delete_address(request.auth, address_id)
    except AppException as e:
        return JsonResponse(
            {"error": True, "code": "address_error", "message": e.detail},
            status=e.status_code,
        )
    return {"detail": "آدرس حذف شد"}


@router.get("/profile", auth=_auth, response=ProfileOut, summary="دریافت پروفایل کاربر")
def get_profile(request):
    return svc.get_profile(request.auth)


@router.patch("/profile", auth=_auth, response=ProfileOut, summary="ویرایش پروفایل کاربر")
def update_profile(request, payload: UpdateProfileIn):
    try:
        return svc.update_profile(
            request.auth,
            payload.full_name,
            payload.email,
            payload.national_id,
        )
    except AppException as e:
        return JsonResponse(
            {"error": True, "code": "profile_error", "message": e.detail},
            status=e.status_code,
        )


@router.get("/orders", auth=_auth, summary="لیست سفارش‌های کاربر")
def my_orders(request):
    from store.services import get_user_orders
    from store.schemas import UserOrderOut
    orders = get_user_orders(request.auth)
    return [UserOrderOut.model_validate(o) for o in orders]


@router.get("/orders/{order_id}", auth=_auth, summary="جزئیات سفارش کاربر")
def my_order_detail(request, order_id: int):
    from store.services import get_user_order_detail
    from store.schemas import UserOrderOut
    try:
        order = get_user_order_detail(request.auth, order_id)
    except AppException as e:
        return JsonResponse(
            {"error": True, "code": "order_not_found", "message": e.detail},
            status=e.status_code,
        )
    return UserOrderOut.model_validate(order)


@router.delete("/orders/{order_id}", auth=_auth, summary="لغو سفارش توسط کاربر")
def cancel_my_order(request, order_id: int):
    """
    لغو سفارش — فقط سفارش‌های با وضعیت «pending» قابل لغو هستند.
    موجودی محصولات به صورت خودکار برگشت داده می‌شود.
    """
    from store.services import cancel_order
    try:
        cancel_order(order_id=order_id, user=request.auth)
    except AppException as e:
        return JsonResponse(
            {"error": True, "code": "cancel_error", "message": e.detail},
            status=e.status_code,
        )
    return {"detail": "سفارش با موفقیت لغو شد"}
