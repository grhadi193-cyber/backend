# Shop API — Backend

فروشگاه آنلاین با Django + Django Ninja. شامل سیستم اطلاع‌رسانی پیشرفته، Shipping هوشمند، پرداخت، OTP Auth و پنل مدیریت کامل.

---

## قابلیت‌ها

### سیستم اطلاع‌رسانی (Notifications)
- قالب‌های قابل شخصی‌سازی برای هر رویداد
- متغیرهای داینامیک (`{user_full_name}`, `{order_id}`, `{postal_tracking}`, ...)
- کانال‌های چندگانه (SMS, Email, WhatsApp, Push)
- فعال/غیرفعال کردن هر پیام
- صف ارسال (Queue) برای مقیاس‌پذیری
- لاگ کامل ارسال‌ها
- ارسال خودکار در رویدادهای: ثبت‌نام، ثبت سفارش، پرداخت، تایید، آماده‌سازی، ارسال، تحویل، لغو

### سیستم Shipping پیشرفته
- مدیریت استان و شهر (31 استان + شهرها)
- تعرفه‌گذاری بر اساس province + city + weight range
- روش‌های ارسال configurable
- API محاسبه هزینه ارسال

### سایر قابلیت‌ها
- OTP Authentication
- Product Catalog با Pagination و Search
- Order Management با Status History
- Payment (Zarinpal + Mock)
- Blog
- Admin Dashboard با Analytics
- Site Settings
- JWT Auth
- SMS (Kavenegar)

---

## نصب و راه‌اندازی

### پیش‌نیازها
- Python 3.11+
- PostgreSQL 14+ (یا SQLite برای توسعه)

### مراحل نصب

```bash
# 1. Clone
https://github.com/grhadi193-cyber/backend.git
cd backend

# 2. Virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Dependencies
pip install -r requirements/local.txt       # Development
# pip install -r requirements/production.txt  # Production

# 4. Environment
cp .env.example .env
# Edit .env with your settings

# 5. Database
python manage.py migrate

# 6. Load provinces & cities
python manage.py load_provinces_cities

# 7. Superuser
python manage.py createsuperuser

# 8. Run
python manage.py runserver
```

### متغیرهای محیطی (.env)

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
# DATABASE_URL=postgres://USER:PASS@HOST:5432/DB
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
KAVENEGAR_API_KEY=your-kavenegar-api-key
SMS_SENDER=your-sender-number
ZARINPAL_MERCHANT_CODE=your-merchant-code
PAYMENT_CALLBACK_BASE_URL=http://127.0.0.1:8000
OTP_EXPIRY_MINUTES=2
```

---

## API Documentation

Swagger UI: http://127.0.0.1:8000/api/docs

مستندات کامل: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

---

## ساختار پروژه

```
backend/
├── accounts/          # User, Address, OTP Auth
├── admin_panel/       # Admin API (dashboard, users, orders, products, analytics)
├── blog/              # Blog posts
├── config/            # Django settings, URLs, WSGI, ASGI
├── core/              # SiteSettings, exceptions, auth
├── notifications/     # Notification system (templates, channels, logs, queue)
├── payment/           # Payment (Zarinpal, Mock)
├── shipping/          # Shipping (methods, zones, provinces, cities, rates)
├── sms/               # SMS service (Kavenegar)
├── store/             # Products, Categories, Orders
├── manage.py
├── requirements/
│   ├── base.txt
│   ├── local.txt
│   └── production.txt
├── .env.example
├── API_DOCUMENTATION.md
├── CURRENT_STATE.md
├── DEPLOY.md
└── README.md
```

---

## Management Commands

```bash
# Process notification queue (run via cron every 1-5 minutes)
python manage.py process_notification_queue --batch-size=50

# Load Iran provinces and cities from JSON
python manage.py load_provinces_cities

# Check for issues
python manage.py check

# Production check
python manage.py check --deploy --settings=config.settings.production
```

---

## Cron Job for Notification Queue

```bash
# /etc/crontab
*/5 * * * * cd /srv/app && source venv/bin/activate && python manage.py process_notification_queue --batch-size=50 >> /var/log/django/notification_queue.log 2>&1
```

---

## Deployment

راهنمای کامل deployment در [DEPLOY.md](DEPLOY.md) موجود است.

---

## License

MIT
