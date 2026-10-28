"""External service configuration, with local-only defaults."""
from django.core.exceptions import ImproperlyConfigured


def web_config(env, local_secret):
    debug = env.get('DJANGO_DEBUG', 'true').lower() in ('true', '1', 'yes')
    key = env.get('DJANGO_SECRET_KEY', '')
    hosts = [host.strip() for host in env.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if host.strip()]
    if not debug:
        if len(key) < 50 or key.startswith('django-insecure-'):
            raise ImproperlyConfigured('Set a private DJANGO_SECRET_KEY of at least 50 characters for production.')
        if not env.get('DJANGO_ALLOWED_HOSTS', '').strip() or not hosts or '*' in hosts:
            raise ImproperlyConfigured('Set explicit DJANGO_ALLOWED_HOSTS for production.')
    return {'secret_key': key or local_secret, 'debug': debug, 'hosts': hosts}


def mailer_config(env):
    host = env.get('SMTP_HOST', '').strip()
    if not host:
        return {'BACKEND': 'django.core.mail.backends.console.EmailBackend'}
    ssl = env.get('SMTP_SSL', 'false').lower() == 'true'
    return {
        'BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
        'OPTIONS': {
            'host': host,
            'port': int(env.get('SMTP_PORT', '465' if ssl else '587')),
            'username': env.get('SMTP_USER', ''),
            'password': env.get('SMTP_PASSWORD', ''),
            'use_ssl': ssl,
            'use_tls': not ssl and env.get('SMTP_TLS', 'true').lower() == 'true',
            'timeout': 15,
        },
    }
