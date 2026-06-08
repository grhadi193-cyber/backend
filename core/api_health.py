"""
Core API - Health checks, version info, and system status
"""
from typing import Dict
from ninja import Router
from django.conf import settings
from django.db import connection
import redis
from datetime import datetime

router = Router(tags=["core"])


@router.get("/health", summary="Health Check", response=Dict)
def health_check(request):
    """
    بررسی سلامت سرویس‌ها
    
    Returns:
        وضعیت دیتابیس، کش و سایر سرویس‌ها
    """
    result = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {}
    }
    
    # Check Database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        result["services"]["database"] = "ok"
    except Exception as e:
        result["services"]["database"] = f"error: {str(e)}"
        result["status"] = "unhealthy"
    
    # Check Redis (if configured)
    redis_url = getattr(settings, 'REDIS_URL', None)
    if redis_url:
        try:
            client = redis.from_url(redis_url)
            client.ping()
            result["services"]["redis"] = "ok"
        except Exception as e:
            result["services"]["redis"] = f"error: {str(e)}"
            result["status"] = "degraded"
    else:
        result["services"]["redis"] = "not configured"
    
    # Check DEBUG mode
    result["debug_mode"] = settings.DEBUG
    if settings.DEBUG:
        result["warnings"] = ["DEBUG mode is enabled - not suitable for production"]
    
    return result


@router.get("/version", summary="Version Info", response=Dict)
def version_info(request):
    """
    اطلاعات نسخه و تنظیمات سیستم
    """
    return {
        "version": "1.0.0",
        "django_version": settings.__class__.__module__,
        "debug": settings.DEBUG,
        "allowed_hosts": settings.ALLOWED_HOSTS,
        "time_zone": settings.TIME_ZONE,
    }


@router.get("/ping", summary="Simple Ping", response=str)
def ping(request):
    """ساده‌ترین endpoint برای بررسی دسترسی"""
    return "pong"
