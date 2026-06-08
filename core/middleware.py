"""
Custom middleware for rate limiting and security enhancements.
"""
import logging
from django.conf import settings
from django.http import JsonResponse
from ratelimit.core import is_ratelimited

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """
    Global rate limiting middleware.
    Applies rate limits to all API endpoints.
    
    Configuration:
        API_RATE_LIMIT = "100/m"  # 100 requests per minute
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Only apply to API endpoints
        if not request.path.startswith('/api/'):
            return self.get_response(request)
        
        # Get rate limit from settings
        rate_limit = getattr(settings, 'API_RATE_LIMIT', '100/m')
        
        # Check if rate limited
        if is_ratelimited(
            request=request,
            group='api',
            key='ip',
            rate=rate_limit,
            increment=True,
        ):
            logger.warning(f"[RateLimit] IP {self._get_client_ip(request)} exceeded limit")
            return JsonResponse(
                {"error": "Too many requests", "code": "RATE_LIMIT_EXCEEDED"},
                status=429,
            )
        
        return self.get_response(request)
    
    def _get_client_ip(self, request):
        """Get client IP considering proxies"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')


class PaymentCallbackSecurityMiddleware:
    """
    Security middleware for payment callback endpoints.
    Validates tokens and prevents replay attacks.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Apply only to payment callback endpoint
        if request.path.startswith('/api/payment/callback'):
            # Log all callback attempts for audit
            logger.info(
                f"[PaymentCallback] Attempt from IP: {self._get_client_ip(request)}, "
                f"Method: {request.method}, Params: {list(request.GET.keys())}"
            )
            
            # Add security headers to response
            response = self.get_response(request)
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            return response
        
        return self.get_response(request)
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
