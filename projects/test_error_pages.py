from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase
from django.views.defaults import bad_request, page_not_found, permission_denied, server_error
from .error_views import csrf_failure


class ErrorPageTests(SimpleTestCase):
    def setUp(self):
        self.request = RequestFactory().get('/missing/')
        self.request.user = AnonymousUser()
        self.request.session = {}

    def test_error_pages_render_with_correct_status_codes(self):
        for handler, status in ((bad_request, 400), (permission_denied, 403), (page_not_found, 404)):
            with self.subTest(status=status):
                response = handler(self.request, Exception('private-error-details'))
                self.assertEqual(response.status_code, status)
                self.assertIn(b'CodeStart', response.content)
                self.assertNotIn(b'private-error-details', response.content)

    def test_server_error_does_not_require_context_processors_or_database(self):
        with patch('projects.context_processors.user_language', side_effect=AssertionError('Must not query database')):
            response = server_error(self.request)
        self.assertEqual(response.status_code, 500)
        self.assertIn(b'CodeStart', response.content)

    def test_not_found_page_respects_uzbek_session(self):
        self.request.session['language'] = 'uz'
        response = page_not_found(self.request, Exception())
        self.assertIn('Sahifa topilmadi'.encode(), response.content)

    def test_csrf_failure_gives_recovery_instructions_without_internal_reason(self):
        response = csrf_failure(self.request, reason='private-csrf-details')
        self.assertEqual(response.status_code, 403)
        self.assertIn('Обновите форму'.encode(), response.content)
        self.assertNotIn(b'private-csrf-details', response.content)
