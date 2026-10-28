from unittest.mock import patch

from django.db import OperationalError
from django.test import TestCase
from django.urls import reverse


class HealthTests(TestCase):
    def test_anonymous_monitor_gets_status_without_template_or_cookie(self):
        response = self.client.get(reverse('health'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})
        self.assertIn('no-store', response['Cache-Control'])
        self.assertFalse(response.cookies)
        self.assertEqual(self.client.head(reverse('health')).status_code, 200)

    def test_database_failure_returns_generic_uncached_503(self):
        with patch('projects.health.connection.cursor', side_effect=OperationalError('private database details')):
            response = self.client.get(reverse('health'))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {'status': 'unavailable'})
        self.assertNotContains(response, 'private database details', status_code=503)
        self.assertIn('no-store', response['Cache-Control'])

    def test_probe_does_not_accept_mutating_methods(self):
        for method in ('post', 'put', 'patch', 'delete'):
            with self.subTest(method=method):
                self.assertEqual(getattr(self.client, method)(reverse('health')).status_code, 405)
