# Shop API Documentation

> **Base URL:** `/api/`  
> **Docs URL:** `/api/docs` (Swagger UI)  
> **Authentication:** JWT Bearer Token (`Authorization: Bearer <token>`)

---

## Table of Contents

- [Core](#core)
- [Auth](#auth)
- [Store](#store)
- [Shipping](#shipping)
- [Payment](#payment)
- [Blog](#blog)
- [Admin](#admin)
- [Notifications](#notifications)

---

## Core

Base path: `/api/`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | No | Health check — returns `{"status": "ok"}` |
| GET | `/settings` | No | Public site settings (name, color, social links, etc.) |

### GET `/settings` Response
```json
{
  "site_name": "فروشگاه من",
  "banner_text": "...",
  "announcement": "...",
  "primary_color": "#01696f",
  "maintenance_mode": false,
  "social_instagram": "...",
  "social_telegram": "...",
  "support_phone": "...",
  "logo": "https://.../media/...",
  "hero_title": "...",
  "hero_text": "...",
  "hero_banner": "https://.../media/...",
  "about_us": "..."
}
```

---

## Auth

Base path: `/api/auth`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/send-otp` | No | Send OTP code to phone number |
| POST | `/verify-otp` | No | Verify OTP and receive JWT token |
| POST | `/login` | No | Login with phone + password |
| POST | `/forgot-password` | No | Request password reset (sends OTP) |
| POST | `/reset-password` | No | Reset password with OTP |
| POST | `/change-password` | Bearer | Change password (old + new) |
| GET | `/profile` | Bearer | Get current user profile |
| PATCH | `/profile` | Bearer | Update profile (name, email, national_id) |
| GET | `/addresses` | Bearer | List user's addresses |
| POST | `/addresses` | Bearer | Add new address |
| DELETE | `/addresses/{id}` | Bearer | Delete an address |
| GET | `/orders` | Bearer | List user's orders |
| GET | `/orders/{id}` | Bearer | Get order details |
| DELETE | `/orders/{id}` | Bearer | Cancel order (only if `pending`) |

### POST `/send-otp`
```json
{
  "phone_number": "09123456789"
}
```

### POST `/verify-otp`
```json
{
  "phone_number": "09123456789",
  "code": "123456"
}
```
**Response:**
```json
{
  "access": "<jwt-access-token>",
  "refresh": "<jwt-refresh-token>"
}
```

### POST `/login`
```json
{
  "phone_number": "09123456789",
  "password": "your_password"
}
```

### POST `/change-password`
```json
{
  "old_password": "old_pass",
  "new_password": "new_pass"
}
```

### POST `/addresses`
```json
{
  "title": "خانه",
  "province": "تهران",
  "city": "تهران",
  "street": "خیابان ...",
  "postal_code": "1234567890",
  "is_default": true
}
```

---

## Store

Base path: `/api/`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/categories` | No | List active categories |
| GET | `/products` | No | List products (pagination + search + filter) |
| GET | `/products/{id}` | No | Product details |
| POST | `/orders` | Bearer | Create new order |

### GET `/products` Query Parameters
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Items per page (max 100) |
| `category_id` | int | — | Filter by category |
| `search` | string | — | Search in name & description |

### POST `/orders`
```json
{
  "address_id": 1,
  "shipping_method_id": 2,
  "items": [
    {
      "product_id": 5,
      "quantity": 2
    }
  ]
}
```
**Response:**
```json
{
  "id": 42,
  "status": "pending",
  "status_display": "درحال تایید",
  "total_price": 1500000,
  "shipping_cost": 50000,
  "tracking_number": "ORD-000042",
  "payment_url": null,
  "items": [
    {
      "product_id": 5,
      "product_name": "...",
      "quantity": 2,
      "unit_price": 500000
    }
  ]
}
```

---

## Shipping

Base path: `/api/shipping`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/methods` | No | List active shipping methods |
| POST | `/options` | No | Calculate shipping options by province name (legacy) |
| GET | `/provinces` | No | List all active provinces |
| GET | `/provinces/{id}/cities` | No | List cities of a province |
| POST | `/calculate` | No | Calculate shipping cost (province_id + city_id + weight) |

### POST `/options` (Legacy)
```json
{
  "province": "تهران",
  "items": [
    {
      "product_id": 5,
      "quantity": 2
    }
  ]
}
```

### POST `/calculate` (Recommended)
```json
{
  "province_id": 8,
  "city_id": 700,
  "total_weight": 2.5,
  "order_total": 1500000
}
```
**Response:**
```json
{
  "province_id": 8,
  "city_id": 700,
  "total_weight": 2.5,
  "order_total": 1500000,
  "options": [
    {
      "id": 1,
      "name": "پست پیشتاز",
      "slug": "post-pishtaz",
      "carrier_name": "پست",
      "tracking_url_template": "https://tracking.post.ir/?code={tracking_code}",
      "cost": 50000,
      "min_days": 3,
      "max_days": 5
    }
  ]
}
```

---

## Payment

Base path: `/api/payment`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/initiate` | Bearer | Start payment for an order |
| GET | `/callback` | No | Gateway callback (Zarinpal redirects here) |

### POST `/initiate`
```json
{
  "order_id": 42
}
```
**Response:**
```json
{
  "payment_url": "https://zarinpal.com/pg/StartPay/...",
  "transaction_id": 15
}
```

### GET `/callback`
Called by payment gateway automatically. Query params:
- `Authority` — Zarinpal authority code
- `Status` — `OK` or `NOK`
- `transaction_id` — Internal transaction ID

---

## Blog

Base path: `/api/blog`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/posts` | No | List published posts |
| GET | `/posts/{slug}` | No | Get post by slug |

---

## Admin

Base path: `/api/admin`  
**All endpoints require `is_staff=True` (AdminBearer)**

### Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard` | Site overview stats (users, orders, revenue) |

### Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users/` | List users (paginated, searchable) |
| GET | `/users/{id}/` | User details |
| PUT | `/users/{id}/` | Update user (name, is_active) |

### Orders

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/orders/` | List all orders (paginated, filterable by status) |
| GET | `/orders/{id}/` | Order details |
| PUT | `/orders/{id}/status/` | Update order status + tracking info |

### Products

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/products/` | List products (paginated, searchable) |
| POST | `/products/` | Create new product |
| GET | `/products/{id}/` | Product details |
| PUT | `/products/{id}/` | Update product |
| PUT | `/products/{id}/stock/` | Update stock (delta quantity) |
| DELETE | `/products/{id}/` | Soft delete (set is_active=False) |

### Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics/overview/` | Revenue & top products report |

### Site Settings

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/settings/` | Get site settings |
| PUT | `/settings/` | Update site settings |

### PUT `/orders/{id}/status/`
```json
{
  "status": "shipped",
  "note": "تحویل به پست",
  "tracking_number": "123456789",
  "postal_tracking": "987654321"
}
```

---

## Notifications

Base path: `/api/notifications/admin`  
**All endpoints require `is_staff=True` (AdminBearer)**

### Channels

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notifications/admin/channels/` | List notification channels |
| POST | `/notifications/admin/channels/` | Create channel |
| GET | `/notifications/admin/channels/{id}/` | Get channel details |
| PUT | `/notifications/admin/channels/{id}/` | Update channel |

### Templates

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notifications/admin/templates/` | List templates |
| POST | `/notifications/admin/templates/` | Create template |
| GET | `/notifications/admin/templates/{id}/` | Get template details |
| PUT | `/notifications/admin/templates/{id}/` | Update template |
| DELETE | `/notifications/admin/templates/{id}/` | Delete template |
| POST | `/notifications/admin/templates/{id}/preview/` | Preview rendered template |
| POST | `/notifications/admin/templates/{id}/send-test/` | Send test notification |

### POST `/notifications/admin/templates/`
```json
{
  "event_type": "order_shipped",
  "channel_id": 1,
  "template_text": "{user_full_name} عزیز، سفارش شما با شماره {order_tracking_number} به پست تحویل شد. کد رهگیری: {postal_tracking}",
  "subject": "",
  "is_active": true,
  "description": "پیامک تحویل به پست"
}
```

### POST `/notifications/admin/templates/{id}/send-test/`
```json
{
  "phone_number": "09123456789",
  "extra_context": {
    "user_full_name": "علی",
    "order_tracking_number": "ORD-000001",
    "postal_tracking": "123456789"
  }
}
```

### Logs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notifications/admin/logs/` | List notification logs (paginated) |
| GET | `/notifications/admin/logs/{id}/` | Get log details |

### GET `/notifications/admin/logs/` Query Parameters
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Items per page |
| `event_type` | string | — | Filter by event type |
| `status` | string | — | Filter by status (pending/sent/failed) |
| `recipient` | string | — | Search by recipient phone |

### Queue

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notifications/admin/queue/` | List queue items |
| POST | `/notifications/admin/queue/process/` | Process pending queue |

### Utilities

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notifications/admin/variables/` | List available template variables |
| GET | `/notifications/admin/event-types/` | List system event types |

### GET `/notifications/admin/variables/` Query Parameters
| Param | Type | Description |
|-------|------|-------------|
| `event_type` | string | Filter by specific event type |

**Response (all events):**
```json
{
  "all_events": {
    "user_registered": ["user_full_name", "user_phone", "site_name"],
    "order_created": ["user_full_name", "order_id", "order_tracking_number", "order_total_price", "order_shipping_cost", "site_name"],
    "order_paid": ["user_full_name", "order_id", "order_tracking_number", "order_total_price", "payment_amount", "site_name"],
    "order_confirmed": ["user_full_name", "order_id", "order_tracking_number", "order_total_price", "site_name"],
    "order_processing": ["user_full_name", "order_id", "order_tracking_number", "site_name"],
    "order_shipped": ["user_full_name", "order_id", "order_tracking_number", "postal_tracking", "carrier_name", "tracking_url", "site_name"],
    "order_delivered": ["user_full_name", "order_id", "order_tracking_number", "site_name"],
    "order_cancelled": ["user_full_name", "order_id", "order_tracking_number", "order_total_price", "site_name"],
    "payment_failed": ["user_full_name", "order_id", "order_tracking_number", "site_name"]
  }
}
```

---

## Shipping Admin Endpoints

Base path: `/api/shipping`  
**All endpoints require `is_staff=True` (AdminBearer)**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/shipping/admin/shipping-methods/` | List all shipping methods |
| GET | `/shipping/admin/shipping-methods/{id}/rates/` | List rates for a method |
| POST | `/shipping/admin/shipping-rates/` | Create shipping rate |
| PUT | `/shipping/admin/shipping-rates/{id}/` | Update shipping rate |
| DELETE | `/shipping/admin/shipping-rates/{id}/` | Delete shipping rate |

### POST `/shipping/admin/shipping-rates/`
```json
{
  "shipping_method_id": 1,
  "province_id": 8,
  "city_id": 700,
  "weight_min": 0,
  "weight_max": 5,
  "cost": 45000
}
```

### PUT `/shipping/admin/shipping-rates/{id}/`
```json
{
  "cost": 50000,
  "is_active": true,
  "weight_min": 0,
  "weight_max": 10
}
```

---

## Authentication

All protected endpoints require this header:
```
Authorization: Bearer <access_token>
```

Tokens are obtained from `POST /api/auth/verify-otp`.

### Admin Endpoints
Admin endpoints additionally require `is_staff=True` on the user.

---

## Response Codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 400 | Bad Request / Validation Error |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (not staff) |
| 404 | Not Found |
| 429 | Too Many Requests (OTP rate limit) |
| 500 | Internal Server Error |

---

## Error Format

```json
{
  "error": true,
  "code": "error_code",
  "message": "Human readable message"
}
```

Common error codes:
- `not_found` — Resource not found
- `validation_error` — Invalid input data
- `duplicate` — Duplicate unique field
- `insufficient_stock` — Not enough product stock
- `otp_error` — OTP sending failed
- `otp_invalid` — Invalid or expired OTP
- `cancel_error` — Order cancellation failed
- `profile_error` — Profile update failed
- `address_error` — Address operation failed
- `order_not_found` — Order not found
- `send_failed` — Notification sending failed
- `invalid_event` — Invalid notification event type

---

## Notification System

### Auto-Triggered Events

| Event | When Triggered | Variables |
|-------|---------------|-----------|
| `user_registered` | After OTP verification (new user) | `{user_full_name}`, `{user_phone}`, `{site_name}` |
| `order_created` | After order is placed | `{user_full_name}`, `{order_id}`, `{order_tracking_number}`, `{order_total_price}`, `{order_shipping_cost}`, `{site_name}` |
| `order_paid` | After successful payment | `{user_full_name}`, `{order_id}`, `{order_tracking_number}`, `{order_total_price}`, `{payment_amount}`, `{site_name}` |
| `order_confirmed` | When admin changes status to `paid` | `{user_full_name}`, `{order_id}`, `{order_tracking_number}`, `{order_total_price}`, `{site_name}` |
| `order_processing` | When admin changes status to `processing` | `{user_full_name}`, `{order_id}`, `{order_tracking_number}`, `{site_name}` |
| `order_shipped` | When admin changes status to `shipped` | `{user_full_name}`, `{order_id}`, `{order_tracking_number}`, `{postal_tracking}`, `{carrier_name}`, `{tracking_url}`, `{site_name}` |
| `order_delivered` | When admin changes status to `delivered` | `{user_full_name}`, `{order_id}`, `{order_tracking_number}`, `{site_name}` |
| `order_cancelled` | When order is cancelled | `{user_full_name}`, `{order_id}`, `{order_tracking_number}`, `{order_total_price}`, `{site_name}` |
| `payment_failed` | When payment fails | `{user_full_name}`, `{order_id}`, `{order_tracking_number}`, `{site_name}` |

### Template Variables

Use `{variable_name}` syntax in templates. Available variables per event type are listed above.

### Queue Processing

Add this to your crontab for automatic queue processing:
```bash
*/5 * * * * cd /srv/app && source venv/bin/activate && python manage.py process_notification_queue --batch-size=50 >> /var/log/django/notification_queue.log 2>&1
```

### Default Channels

| Channel | Default Status | Description |
|---------|---------------|-------------|
| SMS | Active | Uses Kavenegar API |
| Email | Inactive | Placeholder for future |
| WhatsApp | Inactive | Placeholder for future |
| Push | Inactive | Placeholder for future |

---

## Shipping Configuration

### Loading Provinces & Cities

Run once after migration:
```bash
python manage.py load_provinces_cities
```

### Rate Configuration Priority

1. **City-specific rate** — most specific, highest priority
2. **Province-only rate** (city=null) — applies to all cities in province
3. **Method base_cost** — fallback if no rate matches

### Weight-based Pricing

Each `ShippingRate` has `weight_min` and `weight_max`. The system finds the first matching range.

---

## Management Commands

| Command | Description |
|---------|-------------|
| `python manage.py process_notification_queue --batch-size=50` | Process pending notification queue |
| `python manage.py load_provinces_cities` | Load Iran provinces & cities from JSON |
| `python manage.py migrate` | Apply database migrations |
| `python manage.py makemigrations` | Create new migrations |
| `python manage.py createsuperuser` | Create admin user |
| `python manage.py collectstatic` | Collect static files |
| `python manage.py check` | Check for errors |
| `python manage.py runserver` | Start development server |
