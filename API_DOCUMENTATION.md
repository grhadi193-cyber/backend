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
  "code": "12345"
}
```
**Response:**
```json
{
  "access": "<jwt-access-token>",
  "refresh": "<jwt-refresh-token>"
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

---

## Shipping

Base path: `/api/shipping`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/methods` | No | List active shipping methods |
| POST | `/options` | No | Calculate shipping options by province & cart |

### POST `/options`
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

---

## Authentication

All protected endpoints require this header:
```
Authorization: Bearer <access_token>
```

Tokens are obtained from `POST /api/auth/verify-otp`.

---

## Response Codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 400 | Bad Request / Validation Error |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (not staff) |
| 404 | Not Found |
| 402 | Payment Failed |

---

## Error Format

```json
{
  "error": true,
  "code": "error_code",
  "message": "Human readable message"
}
```
