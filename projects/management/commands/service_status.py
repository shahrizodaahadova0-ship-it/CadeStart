from django.conf import settings
from django.core.management.base import BaseCommand

from projects.ai_service import available


class Command(BaseCommand):
    help = 'Show configured service modes without printing credentials or making requests.'

    def handle(self, *args, **options):
        self.stdout.write('AI: configured' if available() else 'AI: reference only (key/model not configured)')
        missing = [name for name in ('OPENAI_API_KEY', 'OPENAI_MODEL') if not getattr(settings, name, '')]
        if missing:
            self.stdout.write('Missing AI settings: ' + ', '.join(missing))
        backend = settings.MAILERS['default']['BACKEND']
        self.stdout.write('Mail: console (local)' if backend.endswith('console.EmailBackend') else 'Mail: external backend configured')
        self.stdout.write('Django: development' if settings.DEBUG else 'Django: production settings')
        self.stdout.write('Configuration only; external connectivity was not tested.')
