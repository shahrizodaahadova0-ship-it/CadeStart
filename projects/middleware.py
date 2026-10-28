from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.utils import timezone
from django.utils import translation

from .models import Profile


class UserTimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        timezone.deactivate()
        language = request.session.get('language', 'ru')
        if request.user.is_authenticated:
            try:
                timezone.activate(ZoneInfo(request.user.profile.timezone))
                language = request.user.profile.language
            except (Profile.DoesNotExist, ZoneInfoNotFoundError, ValueError):
                pass
        try:
            with translation.override(language if language in ('ru', 'uz') else 'ru'):
                return self.get_response(request)
        finally:
            timezone.deactivate()
