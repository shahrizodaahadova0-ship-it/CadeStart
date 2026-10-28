from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class LoginFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('student', password='test')
        self.url = reverse('login')
        self.destination = reverse('lesson', args=['functions']) + '?source=learning'

    def test_destination_survives_failed_login_and_successful_retry(self):
        response = self.client.get(self.url, {'next': self.destination})
        self.assertEqual(response.context['next_url'], self.destination)
        response = self.client.post(self.url, {'username': 'student', 'password': 'wrong', 'next': self.destination})
        self.assertEqual(response.context['next_url'], self.destination)
        self.assertContains(response, 'Неверное имя пользователя или пароль.')
        self.assertRedirects(self.client.post(self.url, {
            'username': 'student', 'password': 'test', 'next': response.context['next_url'],
        }), self.destination)

    def test_external_destinations_are_removed_on_get_and_failed_post(self):
        for destination in ('https://example.com/', '//example.com/', 'javascript:alert(1)', '/\\example.com/'):
            with self.subTest(destination=destination):
                response = self.client.get(self.url, {'next': destination})
                self.assertEqual(response.context['next_url'], '')
                response = self.client.post(self.url, {'username': 'student', 'password': 'wrong', 'next': destination})
                self.assertEqual(response.context['next_url'], '')

    def test_authenticated_user_follows_safe_destination(self):
        self.client.force_login(self.user)
        self.assertRedirects(self.client.get(self.url, {'next': self.destination}), self.destination)
        self.assertRedirects(self.client.get(self.url, {'next': 'https://example.com/'}), reverse('dashboard'))

    def test_successful_login_rejects_external_destination(self):
        self.assertRedirects(self.client.post(self.url, {
            'username': 'student', 'password': 'test', 'next': 'https://example.com/',
        }), reverse('dashboard'))

    def test_relative_destination_is_not_interpreted_as_a_route_name(self):
        response = self.client.post(self.url, {
            'username': 'student', 'password': 'test', 'next': 'unknown-relative-path',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'unknown-relative-path')
        response = self.client.get(self.url, {'next': 'unknown-relative-path'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'unknown-relative-path')

    def test_uzbek_error_and_inactive_account(self):
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])
        session = self.client.session
        session['language'] = 'uz'
        session.save()
        response = self.client.post(self.url, {'username': 'student', 'password': 'test'})
        self.assertContains(response, 'Foydalanuvchi nomi yoki parol noto‘g‘ri.')
        self.assertNotIn('_auth_user_id', self.client.session)
