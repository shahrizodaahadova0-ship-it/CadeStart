"""Render-only configuration; the local development settings stay separate."""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

os.environ.setdefault('DJANGO_DEBUG', 'false')
if not os.environ.get('DJANGO_ALLOWED_HOSTS') and os.environ.get('RENDER_EXTERNAL_HOSTNAME'):
    os.environ['DJANGO_ALLOWED_HOSTS'] = os.environ['RENDER_EXTERNAL_HOSTNAME']

from .settings import *  # noqa: E402,F403

if DEBUG:
    raise ImproperlyConfigured('Render requires DJANGO_DEBUG=false.')
DATA_ROOT = Path(os.environ.get('CODESTART_DATA_DIR', '/var/data'))
if not DATA_ROOT.is_absolute():
    raise ImproperlyConfigured('CODESTART_DATA_DIR must be an absolute persistent disk path.')
DATABASES = {'default': {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': DATA_ROOT / 'db.sqlite3',
    'OPTIONS': {'timeout': 20},
}}
BACKUP_ROOT = DATA_ROOT / 'backups'
# Trust the HTTPS header only in this configuration behind Render's proxy.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
MIDDLEWARE = [*MIDDLEWARE]
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}
