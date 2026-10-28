import json
from smtplib import SMTPException
from unittest.mock import MagicMock, patch
from urllib.error import URLError

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from config.services import mailer_config, web_config
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from io import StringIO
from . import ai_service
from .models import AIConversation, AIMessage


@override_settings(OPENAI_API_KEY='test-key', OPENAI_MODEL='test-model',
                   PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class AIServiceTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user('learner', 'student@example.com', 'test-password')
        self.other = User.objects.create_user('other', password='test-password')
        self.client.force_login(self.user)

    @patch('projects.ai_service.urlopen')
    def test_responses_adapter_uses_server_credentials_and_parses_text(self, mocked):
        response = MagicMock()
        response.read.return_value = json.dumps({'output': [{'type': 'message', 'content': [
            {'type': 'output_text', 'text': 'Use return.'}]}]}).encode()
        mocked.return_value.__enter__.return_value = response
        self.assertEqual(ai_service.answer('Question', [], 'mentor', 'ru'), 'Use return.')
        request = mocked.call_args.args[0]
        payload = json.loads(request.data)
        self.assertFalse(payload['store'])
        self.assertEqual(payload['model'], 'test-model')
        self.assertEqual(payload['input'], [{'role': 'user', 'content': 'Question'}])

    @patch('projects.ai_service.answer', return_value='<script>alert(1)</script> Try return.')
    def test_chat_requires_consent_and_preserves_private_history(self, mocked):
        url = reverse('mentor')
        self.client.post(url, {'question': 'What is return?'})
        mocked.assert_not_called()
        response = self.client.post(url, {'question': 'What is return?', 'consent': 'on'})
        conversation = AIConversation.objects.get(user=self.user)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(conversation.messages.count(), 2)
        response = self.client.get(url, {'conversation': conversation.pk})
        self.assertContains(response, '&lt;script&gt;')
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url, {'conversation': conversation.pk}).status_code, 404)
        self.assertEqual(self.client.post(reverse('delete_conversation', args=[conversation.pk])).status_code, 404)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('delete_conversation', args=[conversation.pk])).status_code, 405)
        self.client.post(reverse('delete_conversation', args=[conversation.pk]))
        self.assertFalse(AIMessage.objects.exists())

    @patch('projects.ai_service.answer', side_effect=ai_service.AIUnavailable('provider_error'))
    def test_provider_failure_keeps_question_without_fake_messages(self, mocked):
        response = self.client.post(reverse('mentor'), {'question': 'Keep this question', 'consent': 'on'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Keep this question')
        self.assertFalse(AIConversation.objects.exists())
        self.assertFalse(AIMessage.objects.exists())
        self.client.post(reverse('mentor'), {'question': 'Too soon', 'consent': 'on'})
        self.assertEqual(mocked.call_count, 1)

    @override_settings(OPENAI_API_KEY='')
    @patch('projects.ai_service.urlopen')
    def test_unconfigured_service_keeps_reference_available_without_request(self, mocked):
        self.assertEqual(self.client.get(reverse('mentor')).status_code, 200)
        self.client.post(reverse('mentor'), {'question': 'No send', 'consent': 'on'})
        mocked.assert_not_called()
        self.assertFalse(AIConversation.objects.exists())

    @patch('projects.ai_service.urlopen', side_effect=URLError('private provider details'))
    def test_adapter_hides_provider_errors(self, mocked):
        with self.assertRaises(ai_service.AIUnavailable) as raised:
            ai_service.answer('Question', [], 'manager', 'uz')
        self.assertEqual(str(raised.exception), 'provider_error')

    def test_smtp_configuration_has_safe_local_default(self):
        self.assertIn('console', mailer_config({})['BACKEND'])
        options = mailer_config({'SMTP_HOST': 'smtp.example.com', 'SMTP_SSL': 'true'})['OPTIONS']
        self.assertEqual(options['port'], 465)
        self.assertTrue(options['use_ssl'])
        self.assertFalse(options['use_tls'])

    @patch('projects.platform_views.send_mail', side_effect=SMTPException('private details'))
    def test_verification_delivery_error_is_reported_without_cooldown(self, mocked):
        response = self.client.post(reverse('email_verification'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'private details')
        self.assertNotIn('verification_sent', self.client.session)

    def test_manager_page_renders_and_cannot_open_mentor_history(self):
        self.assertEqual(self.client.get(reverse('manager')).status_code, 200)
        thread = AIConversation.objects.create(user=self.user, role='mentor', title='Mentor topic')
        self.assertEqual(self.client.get(reverse('manager'), {'conversation': thread.pk}).status_code, 404)


class ConfigurationTests(SimpleTestCase):
    def test_development_keeps_local_secret_and_local_hosts(self):
        config = web_config({}, 'local-secret')
        self.assertTrue(config['debug'])
        self.assertEqual(config['secret_key'], 'local-secret')
        self.assertEqual(config['hosts'], ['localhost', '127.0.0.1'])

    def test_production_requires_private_key_and_explicit_hosts(self):
        with self.assertRaises(ImproperlyConfigured):
            web_config({'DJANGO_DEBUG': 'false'}, 'local-secret')
        env = {'DJANGO_DEBUG': 'false', 'DJANGO_SECRET_KEY': 'a-secure-project-secret-value-with-more-than-fifty-characters', 'DJANGO_ALLOWED_HOSTS': '*'}
        with self.assertRaises(ImproperlyConfigured):
            web_config(env, 'local-secret')
        env['DJANGO_ALLOWED_HOSTS'] = 'codestart.example.com'
        self.assertFalse(web_config(env, 'local-secret')['debug'])

    @override_settings(OPENAI_API_KEY='hidden-test-secret', OPENAI_MODEL='test-model')
    def test_status_command_never_prints_secret(self):
        output = StringIO()
        call_command('service_status', stdout=output)
        self.assertIn('AI: configured', output.getvalue())
        self.assertNotIn('hidden-test-secret', output.getvalue())
