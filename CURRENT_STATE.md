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
- [x] Phase 20 — Hardening v2

## Completed Phases (v3 — Notification + Advanced Shipping)
- [x] Phase 21 — Notification System (Templates, Channels, Queue, Logs)
- [x] Phase 22 — Advanced Shipping (Province, City, Weight-based Rates)
- [x] Phase 23 — API Documentation Complete Update
- [x] Phase 24 — Bug Fixes & Final Review

---

## Existing Apps
- core/         — exceptions, health, SiteSettings
- sms/          — SMSLog, send_otp, send_order_success_sms
- notifications/ — NotificationTemplate, NotificationChannel, NotificationLog, NotificationQueue, auto-triggered events
- accounts/     — User, Address, OTPRecord, auth endpoints
- store/        — Category, Product, ProductImage, Order, OrderItem, OrderStatusHistory
- shipping/     — ShippingZone, ShippingMethod, Province, City, ShippingRate
- payment/      — Transaction, zarinpal provider, mock provider, orchestrator
- blog/         — Post
- admin_panel/  — Admin API + settings endpoints

---

## Model Field Map

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
- name, provinces (JSONField), is_active

### shipping.ShippingMethod
- name, slug, carrier_name, tracking_url_template
- base_cost, cost_per_kg, free_above (null)
- min_days, max_days, zone (FK, null), is_active

### shipping.Province
- name (unique), code, is_active

### shipping.City
- province (FK), name, code, is_active

### shipping.ShippingRate
- shipping_method (FK), province (FK), city (FK, null)
- weight_min, weight_max, cost, is_active

### payment.Transaction
- order (FK), amount, provider, ref_id
- status (pending/success/failed)
- gateway_response (JSONField), callback_token, created_at

### core.SiteSettings
- site_name, logo, banner_text, announcement, primary_color
- maintenance_mode, social_instagram, social_telegram, support_phone
- hero_title, hero_text, hero_banner, about_us

### notifications.NotificationChannel
- name (choices: sms/email/whatsapp/push), is_active, config (JSONField)

### notifications.NotificationTemplate
- event_type, channel (FK)
- subject, template_text, is_active, description

### notifications.NotificationLog
- id (UUID), template (FK), event_type, channel (FK)
- recipient, rendered_message, subject, status
- error_message, sent_at, retry_count, context_data (JSONField)
- user (FK, null), order (FK, null), created_at

### notifications.NotificationQueue
- id (UUID), template (FK), recipient, context_data (JSONField)
- user (FK, null), order (FK, null)
- status, error_message, processed_at, retry_count, created_at

---

## Migration Heads
- accounts:       0010_alter_user_national_id
- store:          0011_remove_order_idempotency_key_alter_product_sku
- shipping:       0003_province_city_shippingrate
- payment:        0003_transaction_callback_token
- core:           0002_site_settings_complete
- sms:            0001_initial
- blog:           0001_initial
- admin_panel:    (no migrations)
- notifications:  0002_default_channels

---

## API Endpoints

### Auth — /api/auth/
- POST /send-otp
- POST /verify-otp
- POST /login
- POST /forgot-password
- POST /reset-password
- POST /change-password
- GET  /profile
- PATCH /profile
- GET  /addresses
- POST /addresses
- DELETE /addresses/{id}
- GET  /orders
- GET  /orders/{id}
- DELETE /orders/{id}

### Store — /api/
- GET /categories
- GET /products (pagination + search)
- GET /products/{id}
- POST /orders

### Shipping — /api/shipping/
- GET  /methods
- POST /options (legacy)
- GET  /provinces
- GET  /provinces/{id}/cities
- POST /calculate

### Shipping Admin — /api/shipping/admin/
- GET  /shipping-methods/
- GET  /shipping-methods/{id}/rates/
- POST /shipping-rates/
- PUT  /shipping-rates/{id}/
- DELETE /shipping-rates/{id}/

### Payment — /api/payment/
- POST /initiate
- GET  /callback

### Blog — /api/blog/
- GET /posts
- GET /posts/{slug}

### Core — /api/
- GET /health
- GET /settings

### Admin — /api/admin/
- GET /dashboard
- GET /users/
- GET /users/{id}/
- PUT /users/{id}/
- GET /orders/
- GET /orders/{id}/
- PUT /orders/{id}/status/
- GET /products/
- POST /products/
- GET /products/{id}/
- PUT /products/{id}/
- PUT /products/{id}/stock/
- DELETE /products/{id}/
- GET /analytics/overview/
- GET /settings/
- PUT /settings/

### Notifications Admin — /api/notifications/admin/
- GET  /channels/
- POST /channels/
- GET  /channels/{id}/
- PUT  /channels/{id}/
- GET  /templates/
- POST /templates/
- GET  /templates/{id}/
- PUT  /templates/{id}/
- DELETE /templates/{id}/
- GET  /logs/
- GET  /logs/{id}/
- GET  /queue/
- POST /queue/process/
- GET  /variables/
- GET  /event-types/
- POST /templates/{id}/preview/
- POST /templates/{id}/send-test/

---

## Notification Auto-Triggered Events
1. `user_registered` — After new user OTP verification
2. `order_created` — After order placement
3. `order_paid` — After successful payment
4. `order_confirmed` — Status → paid
5. `order_processing` — Status → processing
6. `order_shipped` — Status → shipped
7. `order_delivered` — Status → delivered
8. `order_cancelled` — Order cancellation

---

## Settings Constants
- `DEFAULT_PAGE_SIZE = 20`
- `MAX_PAGE_SIZE = 100`
- `OTP_EXPIRY_MINUTES` (env)
- `OTP_RATE_LIMIT_SECONDS = 60`
- `CORS_ALLOWED_ORIGINS` (env)

---

## Management Commands
- `python manage.py process_notification_queue --batch-size=50`
- `python manage.py load_provinces_cities`
- `python manage.py migrate`
- `python manage.py makemigrations`
- `python manage.py createsuperuser`
- `python manage.py collectstatic`
- `python manage.py check`
- `python manage.py runserver`

---

## Project Status
✅ پروژه آماده production است.
✅ سیستم اطلاع‌رسانی کامل با قابلیت شخصی‌سازی
✅ سیستم Shipping پیشرفته با province/city/weight
✅ API Documentation کامل و به‌روز
