from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from uuid import uuid4

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from projects.backups import backup_database


class Command(BaseCommand):
    help = 'Create and verify a consistent SQLite backup without overwriting existing files.'

    def add_arguments(self, parser):
        parser.add_argument('--output', help='New backup file path; defaults to backups/.')

    def handle(self, *args, **options):
        database = settings.DATABASES['default']
        if database['ENGINE'] != 'django.db.backends.sqlite3':
            raise CommandError('This command supports SQLite only.')
        name = f"codestart-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid4().hex[:8]}.sqlite3"
        destination = options.get('output') or Path(getattr(settings, 'BACKUP_ROOT', Path(settings.BASE_DIR) / 'backups')) / name
        try:
            result = backup_database(database['NAME'], destination)
        except (OSError, ValueError, sqlite3.Error) as exc:
            raise CommandError(f'Backup failed: {exc}') from exc
        self.stdout.write(self.style.SUCCESS(f'Backup verified: {result}'))
