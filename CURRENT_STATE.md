# CURRENT_STATE

## Environment
- Local OS: Windows
- Mode: development (split settings)
- Target: Linux server
- Testing: Swagger UI

## Completed Phases (v1)
- [x] Phase 01 Bootstrap
- [x] Phase 02 Core
- [x] Phase 03 SMS
- [x] Phase 04 Accounts (User + Address)
- [x] Phase 05 OTP Auth
- [x] Phase 06 Store Catalog
- [x] Phase 07 Shipping (basic)
- [x] Phase 08 Orders
- [x] Phase 09 Payment (zarinpal + mock)
- [x] Phase 10 Blog
- [x] Phase 11 Hardening

## Completed Phases (v2 — اصلاحیه)
- [x] Phase 12 — Account Profile + کد ملی + آدرس کامل
- [x] Phase 13 — Order Tracking + OrderStatusHistory
- [x] Phase 14 — Product Gallery + بهبود مدل محصول
- [x] Phase 15 — Smart Shipping (Zone + Weight)
- [x] Phase 16 — Payment Refactor (Orchestrator + Providers)
- [x] Phase 17 — Admin API کامل
- [x] Phase 18 — SiteSettings کامل
- [x] Phase 19 — Pagination + Search
- [x] Phase 20 — Hardening v2 ✅

## Existing Apps
- core/        — exceptions, health, SiteSettings (کامل — فاز 18)
- sms/         — SMSLog, send_otp, send_order_success_sms
- accounts/    — User, Address, OTPRecord, auth endpoints
- store/       — Category, Product, ProductImage, Order, OrderItem, OrderStatusHistory
- shipping/    — ShippingZone, ShippingMethod
- payment/     — Transaction, zarinpal provider, mock provider, orchestrator
- blog/        — Post
- admin_panel/ — Admin API کامل (فاز 17) + settings endpoints (فاز 18)

---

## Model Field Map (وضعیت دقیق فیلدها)

### accounts.User
- phone_number (unique)
- full_name
- email (null, unique)
- national_id (null, unique)
- is_active, is_staff, date_joined

### accounts.Address
- user (FK)
- title, province, city, street, postal_code, is_default

### accounts.OTPRecord
- phone_number (unique), code, created_at, expires_at, is_used, last_sent_at

### store.Category
- name, slug, description, image, is_active, created_at

### store.Product
- category (FK, null)
- name, slug, description
- price, discount_price (null)
- sku (null, unique), meta_title, meta_description, view_count
- stock, weight, image, is_active, created_at, updated_at

### store.ProductImage
- product (FK), image, alt_text, order, is_cover

### store.Order
- user (FK), address (FK), shipping_method (FK)
- status (pending/paid/processing/shipped/delivered/cancelled)
- total_price, shipping_cost
- tracking_number, postal_tracking, carrier_name
- shipped_at, delivered_at, customer_notes
- shipping_address_snapshot (JSONField)
- created_at

### store.OrderItem
- order (FK), product (FK)
- product_name_snapshot, quantity, unit_price

### store.OrderStatusHistory
- order (FK), status, note, created_at, created_by (FK User, null)

### shipping.ShippingZone
- name, provinces (JSONField)

### shipping.ShippingMethod
- name, slug, base_cost, cost_per_kg, free_above (null)
- min_days, max_days, zone (FK, null), is_active

### payment.Transaction
- order (FK), amount, provider, ref_id
- status (pending/success/failed)
- gateway_response (JSONField), created_at

### core.SiteSettings
- site_name (default="فروشگاه من")
- logo (ImageField, null/blank)
- banner_text
- announcement
- primary_color (default="#01696f")
- maintenance_mode (BooleanField)
- social_instagram (URLField)
- social_telegram (URLField)
- support_phone
- hero_title (legacy)
- hero_text (legacy)
- hero_banner (legacy, ImageField)
- about_us (legacy)

---

## Migration Heads (آخرین migration هر app)
- accounts:    0009_alter_user_national_id
- store:       0008_product_discount_price_product_meta_description_and_more
- shipping:    0002_shippingzone_shippingmethod_cost_per_kg_and_more
- payment:     0002_transaction_provider
- core:        0002_site_settings_complete
- sms:         0001_initial
- blog:        0001_initial
- admin_panel: (no migrations — بدون مدل)

> ⚠️ فاز 20 هیچ migration جدیدی ندارد.
> خروجی `makemigrations --check` باید `No changes detected` باشد.

---

## API Endpoints (وضعیت فعلی)

### Auth — /api/auth/
- POST /send-otp
- POST /verify-otp
- GET  /profile
- PATCH /profile  (full_name, email, national_id)
- GET  /addresses
- POST /addresses
- DELETE /addresses/{id}
- GET  /orders
- GET  /orders/{id}
- DELETE /orders/{id}  ← لغو سفارش (فقط pending) + برگشت موجودی

### Store — /api/
- GET /categories
- GET /products            ← pagination + search (فاز 19)
- GET /products/{id}
- POST /orders (auth)

### Shipping — /api/shipping/
- GET  /methods
- POST /options

### Payment — /api/payment/
- POST /initiate (auth)
- GET  /callback
- GET  /mock-callback (DEBUG only)

### Blog — /api/blog/
- (endpoints موجود)

### Core — /api/
- GET /health
- GET /settings          ← عمومی، بدون auth (فاز 18)

### Admin — /api/admin/
#### داشبورد
- GET /dashboard

#### مدیریت کاربران
- GET  /users/
- GET  /users/{id}/
- PUT  /users/{id}/

#### مدیریت سفارش‌ها
- GET  /orders/
- GET  /orders/{id}/
- PUT  /orders/{id}/status/

#### مدیریت محصولات
- GET    /products/
- POST   /products/
- GET    /products/{id}/
- PUT    /products/{id}/
- PUT    /products/{id}/stock/
- DELETE /products/{id}/

#### آنالیتیکس
- GET /analytics/overview/

#### تنظیمات سایت (فاز 18)
- GET /settings/
- PUT /settings/

---

## Settings Constants (فاز 20)
- `DEFAULT_PAGE_SIZE = 20`       — پیش‌فرض صفحه‌بندی
- `MAX_PAGE_SIZE = 100`          — حداکثر تعداد در هر صفحه
- `OTP_EXPIRY_MINUTES` (env)     — پیش‌فرض: 2 دقیقه
- `OTP_RATE_LIMIT_SECONDS = 60`  — فاصله بین ارسال‌های OTP
- `CORS_ALLOWED_ORIGINS` (env)   — پیش‌فرض: [] (در production باید تنظیم شود)

---

## Hardening v2 — فاز 20
- OTP rate-limit از `settings.OTP_RATE_LIMIT_SECONDS` خوانده می‌شود (نه عدد ثابت)
- `OTP_EXPIRY_MINUTES` در `.env.example` مستند شد
- `/error-test` endpoint از core/api.py حذف شد
- `whitenoise` تکراری از `requirements/production.txt` حذف شد
- `CORS_ALLOWED_ORIGINS` default به `[]` تغییر کرد (production-safe)
- `DEPLOY.md` با جدول env variables کامل شد

---

## Known Issues / ناقص‌ها
- store/api.py و payment/api.py هر دو AuthBearer تعریف کرده‌اند (تکراری — قابل refactor در آینده)
- debug_toolbar: خطای template بی‌خطر در ترمینال

## Last Successful Commands
```
python apply_phase_20.py
python manage.py check              → 0 issues
python manage.py makemigrations --check  → No changes detected
python manage.py migrate            → No new migrations
python manage.py runserver          → OK
python manage.py check --settings=config.settings.production → OK
```

## Project Status
✅ پروژه آماده production است.
