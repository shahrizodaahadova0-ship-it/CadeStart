from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import LessonProgress


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class LessonRepeatTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('student', password='test')
        self.other = User.objects.create_user('other', password='test')
        self.client.force_login(self.user)
        self.url = reverse('lesson', args=['functions'])

    def test_reopen_keeps_notes_and_quiz_and_changes_progress(self):
        progress = LessonProgress.objects.create(user=self.user, lesson='functions', code='Saved notes',
                                                 completed=True, quiz_score=100, quiz_answers={'answer_0': '2'})
        self.assertContains(self.client.get(self.url), 'Вернуться к повторению')
        self.client.post(self.url, {'action': 'reopen', 'code': 'Do not overwrite notes'})
        progress.refresh_from_db()
        self.assertFalse(progress.completed)
        self.assertEqual(progress.code, 'Saved notes')
        self.assertEqual(progress.quiz_score, 100)
        self.assertEqual(progress.quiz_answers, {'answer_0': '2'})
        self.assertEqual(self.client.get(reverse('results')).context['completed'], 0)

    def test_reopen_cannot_change_another_users_progress(self):
        progress = LessonProgress.objects.create(user=self.other, lesson='functions', completed=True)
        self.client.post(self.url, {'action': 'reopen'})
        progress.refresh_from_db()
        self.assertTrue(progress.completed)
        self.assertFalse(LessonProgress.objects.filter(user=self.user).exists())

    def test_unknown_actions_and_missing_code_do_not_erase_notes(self):
        progress = LessonProgress.objects.create(user=self.user, lesson='functions', code='Keep notes')
        self.assertEqual(self.client.post(self.url, {'action': 'unknown'}).status_code, 400)
        self.client.post(self.url, {'action': 'complete'})
        progress.refresh_from_db()
        self.assertTrue(progress.completed)
        self.assertEqual(progress.code, 'Keep notes')

    def test_oversized_notes_are_kept_in_form_without_changing_saved_progress(self):
        progress = LessonProgress.objects.create(user=self.user, lesson='functions', code='Keep notes')
        oversized = 'x' * 20001
        response = self.client.post(self.url, {'action': 'complete', 'code': oversized})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['code'], oversized)
        self.assertContains(response, 'Заметки не сохранены')
        progress.refresh_from_db()
        self.assertEqual(progress.code, 'Keep notes')
        self.assertFalse(progress.completed)
        self.client.post(self.url, {'action': 'save', 'code': 'x' * 20000})
        progress.refresh_from_db()
        self.assertEqual(len(progress.code), 20000)

    def test_oversized_notes_do_not_create_progress(self):
        self.client.post(self.url, {'action': 'save', 'code': 'x' * 20001})
        self.assertFalse(LessonProgress.objects.filter(user=self.user).exists())
