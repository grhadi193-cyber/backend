from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from ninja import NinjaAPI

api = NinjaAPI(title="Shop API", version="1.0.0", docs_url="/docs")

# -- Routers ------------------------------------------------------------------
from core.api            import router as core_router
from accounts.api        import router as accounts_router
from store.api           import router as store_router
from shipping.api        import router as shipping_router
from payment.api         import router as payment_router
from blog.api            import router as blog_router
from admin_panel.api     import router as admin_router
from notifications.api   import router as notifications_router

api.add_router("/",             core_router)
api.add_router("/auth",         accounts_router)
api.add_router("/",             store_router)
api.add_router("/shipping",     shipping_router)
api.add_router("/payment",      payment_router)
api.add_router("/blog",         blog_router)
api.add_router("/admin",        admin_router)
api.add_router("/notifications", notifications_router)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/",   api.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    try:
        from django.urls import include
        import debug_toolbar
        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass
