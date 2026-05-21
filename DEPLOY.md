# Deployment Guide — Linux Production Server

## Prerequisites

| Item | Version |
|------|---------|
| Python | 3.11+ |
| PostgreSQL | 14+ |
| Nginx | 1.24+ (reverse proxy) |
| OS | Ubuntu 22.04 LTS (recommended) |

---

## 1 — First-time server setup

```bash
# Create a dedicated system user (no login shell)
sudo adduser --system --group --no-create-home appuser

# Create directories
sudo mkdir -p /srv/app /var/log/django /srv/app/media
sudo chown appuser:appuser /srv/app /var/log/django /srv/app/media
```

---

## 2 — Clone / pull the repository

```bash
cd /srv/app
# First deploy:
git clone https://github.com/YOUR_ORG/YOUR_REPO.git .

# Subsequent deploys:
git pull origin main
```

---

## 3 — Python virtual environment

```bash
python3 -m venv /srv/app/venv
source /srv/app/venv/bin/activate
pip install --upgrade pip
pip install -r requirements/production.txt
```

---

## 4 — Environment variables

Copy `.env.example` to `/srv/app/.env` and fill in every value, **or**
export variables directly in the systemd service (recommended for secrets):

```bash
cp .env.example .env
nano .env          # fill in SECRET_KEY, DATABASE_URL, ALLOWED_HOSTS, etc.
chmod 600 .env     # restrict read access
```

> **Mandatory for production:**
> `SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`

> **Tip:** Generate a strong SECRET_KEY:
> ```bash
> python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
> ```

---

## 5 — Database

```bash
export DJANGO_SETTINGS_MODULE=config.settings.production

# Run migrations
python manage.py migrate --noinput

# Create superuser (first deploy only)
python manage.py createsuperuser
```

---

## 6 — Static files

```bash
python manage.py collectstatic --noinput
```

WhiteNoise serves `staticfiles/` directly from gunicorn — no separate
Nginx `alias` needed for static files.

---

## 7 — Sanity check

```bash
python manage.py check --deploy --settings=config.settings.production
```

All issues flagged here must be resolved before going live.

---

## 8 — Gunicorn (run manually to test)

```bash
gunicorn config.wsgi:application \
  --workers 3 \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile /var/log/django/gunicorn_access.log \
  --error-logfile  /var/log/django/gunicorn_error.log
```

Worker formula: `(2 × CPU cores) + 1`

---

## 9 — Systemd service (recommended)

Create `/etc/systemd/system/app.service`:

```ini
[Unit]
Description=Django App (gunicorn)
After=network.target postgresql.service

[Service]
User=appuser
Group=appuser
WorkingDirectory=/srv/app
EnvironmentFile=/srv/app/.env
Environment="DJANGO_SETTINGS_MODULE=config.settings.production"
ExecStart=/srv/app/venv/bin/gunicorn config.wsgi:application \
          --workers 3 \
          --bind unix:/run/app.sock \
          --timeout 120 \
          --access-logfile /var/log/django/gunicorn_access.log \
          --error-logfile  /var/log/django/gunicorn_error.log
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable app
sudo systemctl start app
sudo systemctl status app
```

---

## 10 — Nginx reverse proxy

`/etc/nginx/sites-available/app`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate     /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    client_max_body_size 20M;

    location /media/ {
        alias /srv/app/media/;
    }

    location / {
        proxy_pass         http://unix:/run/app.sock;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 120;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 11 — TLS certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Auto-renewal is set up by certbot automatically.

---

## 12 — Routine deploy checklist

```bash
# On the server
cd /srv/app
source venv/bin/activate

git pull origin main
pip install -r requirements/production.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
sudo systemctl restart app
sudo systemctl status app
```

---

## 13 — Log files

| File | Content |
|------|---------|
| `/var/log/django/django.log` | All WARNING+ application events |
| `/var/log/django/django_errors.log` | ERROR+ only (alerts / crashes) |
| `/var/log/django/gunicorn_access.log` | HTTP access log |
| `/var/log/django/gunicorn_error.log` | Gunicorn worker errors |

---

## 14 — Rollback

```bash
git log --oneline -10          # find the last good commit
git checkout <COMMIT_HASH>
python manage.py migrate --noinput   # if migrations rolled back
sudo systemctl restart app
```

---

## 15 — Environment variables reference

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | ✅ | Django secret key (min 50 chars) |
| `DEBUG` | ✅ | `False` in production |
| `DATABASE_URL` | ✅ | `postgres://USER:PASS@HOST:5432/DB` |
| `ALLOWED_HOSTS` | ✅ | Comma-separated hostnames |
| `CORS_ALLOWED_ORIGINS` | ✅ | Comma-separated frontend origins |
| `KAVENEGAR_API_KEY` | ✅ | SMS gateway API key |
| `ZARINPAL_MERCHANT_CODE` | ✅ | Payment gateway merchant ID |
| `PAYMENT_CALLBACK_BASE_URL` | ✅ | Public base URL for payment callbacks |
| `OTP_EXPIRY_MINUTES` | — | Default: `2` |
| `SECURE_SSL_REDIRECT` | — | Default: `True` |
| `SECURE_HSTS_SECONDS` | — | Default: `31536000` |
| `DB_CONN_MAX_AGE` | — | Default: `60` |
| `LOG_DIR` | — | Default: `BASE_DIR/logs` |
| `DJANGO_LOG_LEVEL` | — | Default: `WARNING` |
