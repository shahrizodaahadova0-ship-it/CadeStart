"""Validate the external PostgreSQL URL without including credentials in errors."""
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured


def postgres_database(value):
    import dj_database_url

    try:
        if urlsplit(value).scheme not in ('postgres', 'postgresql'):
            raise ValueError
        database = dj_database_url.parse(value, conn_max_age=60, conn_health_checks=True)
        if not all(database.get(key) for key in ('HOST', 'NAME', 'USER')):
            raise ValueError
        options = database.setdefault('OPTIONS', {})
        options.setdefault('sslmode', 'require')
        if options['sslmode'] not in ('require', 'verify-ca', 'verify-full'):
            raise ValueError
        options.setdefault('connect_timeout', 10)
        return database
    except (ValueError, TypeError, KeyError):
        raise ImproperlyConfigured('Set DATABASE_URL to a complete PostgreSQL connection URL with TLS enabled.') from None
