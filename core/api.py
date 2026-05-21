from typing import Optional

from ninja import Router
from pydantic import BaseModel

router = Router(tags=["core"])


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────

class SiteSettingsOut(BaseModel):
    site_name:        str
    banner_text:      str
    announcement:     str
    primary_color:    str
    maintenance_mode: bool
    social_instagram: str
    social_telegram:  str
    support_phone:    str
    logo:             Optional[str] = None
    # فیلدهای legacy
    hero_title:  str
    hero_text:   str
    hero_banner: Optional[str] = None
    about_us:    str

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/health", summary="Health check")
def health(request):
    """Returns 200 OK — used by load-balancers and CI."""
    return {"status": "ok"}


@router.get("/settings", response=SiteSettingsOut, summary="تنظیمات عمومی سایت")
def get_site_settings(request):
    """
    تنظیمات سایت — عمومی، بدون نیاز به auth.
    فرانت‌اند برای رنگ، نام، پیام‌ها و شبکه‌های اجتماعی از اینجا می‌خواند.
    """
    from core.models import SiteSettings
    s = SiteSettings.get()

    def _url(field):
        if field and hasattr(field, "url"):
            try:
                return request.build_absolute_uri(field.url)
            except Exception:
                return None
        return None

    return SiteSettingsOut(
        site_name        = s.site_name,
        banner_text      = s.banner_text,
        announcement     = s.announcement,
        primary_color    = s.primary_color,
        maintenance_mode = s.maintenance_mode,
        social_instagram = s.social_instagram,
        social_telegram  = s.social_telegram,
        support_phone    = s.support_phone,
        logo             = _url(s.logo),
        hero_title       = s.hero_title,
        hero_text        = s.hero_text,
        hero_banner      = _url(s.hero_banner),
        about_us         = s.about_us,
    )
