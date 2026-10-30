from importlib.util import find_spec
from unittest import skipUnless

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from config.postgres import postgres_database


@skipUnless(find_spec('dj_database_url'), 'Install requirements-render-free.txt to test PostgreSQL configuration.')
class PostgresConfigurationTests(SimpleTestCase):
    def test_complete_url_preserves_encoded_password_and_requires_tls(self):
        database = postgres_database('postgresql://student:p%40ss%3Aword@db.example.com/neondb?sslmode=require&channel_binding=require')
        self.assertEqual(database['ENGINE'], 'django.db.backends.postgresql')
        self.assertEqual(database['PASSWORD'], 'p@ss:word')
        self.assertEqual(database['OPTIONS']['sslmode'], 'require')
        self.assertEqual(database['OPTIONS']['channel_binding'], 'require')
        self.assertTrue(database['CONN_HEALTH_CHECKS'])

    def test_missing_or_invalid_url_does_not_expose_credentials(self):
        for value in ('', 'sqlite:///db.sqlite3', 'postgres://student:private-value@/db',
                      'postgres://student:private-value@db.example.com/db?sslmode=disable'):
            with self.subTest(value=value), self.assertRaises(ImproperlyConfigured) as raised:
                postgres_database(value)
            self.assertNotIn('private-value', str(raised.exception))

    def test_tls_defaults_to_required(self):
        self.assertEqual(postgres_database('postgres://student:test@db.example.com/db')['OPTIONS']['sslmode'], 'require')
