"""Render local QA artifacts without adding users or changing project data."""
import os
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.contrib.auth.models import AnonymousUser, User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory
from django.urls import resolve
from projects.models import Profile

root = Path(__file__).resolve().parent
out = root / 'artifacts'
out.mkdir(exist_ok=True)
css = (root / 'projects/static/projects/app.css').read_text(encoding='utf-8')
js = (root / 'projects/static/projects/app.js').read_text(encoding='utf-8')
factory = RequestFactory()
for name, url in [('home', '/'), ('dashboard', '/dashboard/'), ('mentor', '/mentor/'), ('kanban', '/company/tasks/')]:
    request = factory.get(url)
    request.session = {}
    request._messages = FallbackStorage(request)
    if name == 'home':
        request.user = AnonymousUser()
    else:
        request.user = User(pk=99999999, username='Abror', first_name='Abror')
        request.user.profile = Profile(user=request.user, language='ru', onboarded=True)
    match = resolve(url)
    request.resolver_match = match
    response = match.func(request, **match.kwargs)
    html = response.content.decode('utf-8')
    html = html.replace('<link rel="stylesheet" href="/static/projects/app.css">', f'<style>{css}</style>')
    html = html.replace('<script src="/static/projects/app.js" defer></script>', f'<script>{js}</script>')
    (out / f'{name}.html').write_text(html, encoding='utf-8')
print('QA HTML saved in artifacts/. No application data changed.')
