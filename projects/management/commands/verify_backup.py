import sqlite3

from django.core.management.base import BaseCommand, CommandError

from projects.backups import verify_backup


class Command(BaseCommand):
    help = 'Check a SQLite backup without changing the file or live database.'

    def add_arguments(self, parser):
        parser.add_argument('path')

    def handle(self, *args, **options):
        try:
            verify_backup(options['path'])
        except (OSError, ValueError, sqlite3.Error) as exc:
            raise CommandError(f'Invalid backup: {exc}') from exc
        self.stdout.write(self.style.SUCCESS('SQLite integrity check: OK'))
