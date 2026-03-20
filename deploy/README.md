# Deploy

This project is prepared for deployment on a Linux VPS with `gunicorn` and `nginx`.

## Expected layout

- Project path: `/var/www/elib_vkr_validation`
- Virtualenv path: `/var/www/elib_vkr_validation/venv`
- Gunicorn bind: `127.0.0.1:8000`

## Basic steps

1. Copy the project to `/var/www/elib_vkr_validation`
2. Create `.env` from `.env.example`
3. Install dependencies
4. Run migrations and collectstatic
5. Enable `deploy/gunicorn.service`
6. Enable `deploy/animatg.online.nginx.conf`
7. Issue HTTPS certificate with Certbot
