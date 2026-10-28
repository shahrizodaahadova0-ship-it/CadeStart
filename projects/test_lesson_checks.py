from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import LessonProgress


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class LessonCheckTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('student', password='test')
        self.other = User.objects.create_user('other', password='test')
        self.client.force_login(self.user)
        self.url = reverse('lesson', args=['functions'])

    def test_check_is_graded_on_server_and_preserves_draft_and_completion(self):
        progress = LessonProgress.objects.create(user=self.user, lesson='functions', code='My saved notes', completed=True)
        self.client.post(self.url, {'action': 'check', 'answer_0': '0', 'quiz_score': 100, 'code': 'Overwrite attempt'})
        progress.refresh_from_db()
        self.assertEqual(progress.quiz_score, 0)
        self.assertEqual(progress.code, 'My saved notes')
        self.assertTrue(progress.completed)
        self.client.post(self.url, {'action': 'check', 'answer_0': '2'})
        progress.refresh_from_db()
        self.assertEqual(progress.quiz_score, 100)
        self.assertEqual(LessonProgress.objects.filter(user=self.user, lesson='functions').count(), 1)

    def test_unanswered_check_is_not_saved_and_correct_check_does_not_complete_lesson(self):
        response = self.client.post(self.url, {'action': 'check'})
        self.assertIn('answer_0', response.context['quiz_form'].errors)
        self.assertFalse(LessonProgress.objects.exists())
        self.client.post(self.url, {'action': 'check', 'answer_0': '2'})
        progress = LessonProgress.objects.get(user=self.user)
        self.assertFalse(progress.completed)
        self.assertEqual(progress.quiz_answers, {'answer_0': '2'})
        self.client.force_login(self.other)
        self.assertIsNone(self.client.get(self.url).context['progress'])

    def test_explanations_and_uzbek_questions_render(self):
        self.client.post(self.url, {'action': 'check', 'answer_0': '0'})
        response = self.client.get(self.url)
        self.assertContains(response, 'при x=4 результат равен 8')
        self.user.profile.language = 'uz'
        self.user.profile.save()
        response = self.client.get(self.url)
        self.assertContains(response, 'Funksiyalar')
        self.assertContains(response, 'x=4 bo‘lsa, natija 8')

    def test_ordinary_draft_save_does_not_forge_quiz_result(self):
        self.client.post(self.url, {'action': 'save', 'code': 'notes', 'quiz_score': 100})
        self.assertIsNone(LessonProgress.objects.get(user=self.user).quiz_score)

    def test_checks_appear_in_private_report_and_navigation_stays_in_curriculum(self):
        self.client.post(self.url, {'action': 'check', 'answer_0': '2'})
        payload = self.client.get(reverse('report'), {'format': 'json'}).json()
        self.assertEqual(payload['lesson_checks'], [{'lesson': 'functions', 'title': 'Работа с функциями', 'score': 100}])
        response = self.client.get(self.url)
        self.assertEqual(response.context['previous_lesson']['slug'], 'collections')
        self.assertEqual(response.context['next_lesson']['slug'], 'errors')
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse('report'), {'format': 'json'}).json()['lesson_checks'], [])
