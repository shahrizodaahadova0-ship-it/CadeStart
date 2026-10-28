"""Prepare the mounted database, then replace this process with Gunicorn."""
import os
import subprocess
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.render_settings')
    import django
    django.setup()
    from django.conf import settings

    settings.DATA_ROOT.mkdir(parents=True, exist_ok=True)
    if settings.DATABASES['default']['NAME'].exists():
        subprocess.run([sys.executable, 'manage.py', 'backup_database'], check=True)
    subprocess.run([sys.executable, 'manage.py', 'migrate', '--noinput'], check=True)
    port = int(os.environ.get('PORT', '10000'))
    os.execvp(sys.executable, [sys.executable, '-m', 'gunicorn', 'config.wsgi:application',
                             '--bind', f'0.0.0.0:{port}', '--workers', '1', '--threads', '4',
                             '--timeout', '90', '--access-logfile', '-', '--error-logfile', '-'])


if __name__ == '__main__':
    main()
