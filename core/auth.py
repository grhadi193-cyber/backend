"""
Centralized JWT authentication classes for Django Ninja.

Usage:
    from core.auth import AuthBearer, AdminBearer

    @router.get("/endpoint", auth=AuthBearer())
    def my_view(request): ...

    @router.get("/admin-endpoint", auth=AdminBearer())
    def admin_view(request): ...
"""
from ninja.security import HttpBearer


class AuthBearer(HttpBearer):
    """Validates a JWT Bearer token and returns the authenticated User."""

    def authenticate(self, request, token):
        from rest_framework_simplejwt.tokens import AccessToken
        from rest_framework_simplejwt.exceptions import TokenError
        try:
            validated = AccessToken(token)
            from accounts.models import User
            return User.objects.get(pk=validated["user_id"])
        except (TokenError, Exception):
            return None


class AdminBearer(HttpBearer):
    """Validates a JWT Bearer token and returns the User only if is_staff=True."""

    def authenticate(self, request, token):
        from rest_framework_simplejwt.tokens import AccessToken
        from rest_framework_simplejwt.exceptions import TokenError
        try:
            validated = AccessToken(token)
            from accounts.models import User
            user = User.objects.get(pk=validated["user_id"])
            if not user.is_staff:
                return None
            return user
        except (TokenError, Exception):
            return None
