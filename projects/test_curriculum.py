from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .catalog import LESSONS
from .models import LessonContent, LessonProgress


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class CurriculumTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user('student', password='test')
        self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'test')
        self.client.force_login(self.student)

    def test_seeded_curriculum_matches_existing_lessons(self):
        self.assertEqual(LessonContent.objects.count(), len(LESSONS))
        self.assertEqual(LessonContent.objects.get(slug='functions').title, 'Работа с функциями')

    def test_content_updates_are_visible_without_changing_progress_or_checks(self):
        progress = LessonProgress.objects.create(user=self.student, lesson='functions', completed=True,
                                                 code='My private draft', quiz_score=100)
        content = LessonContent.objects.get(slug='functions')
        content.title = 'Функции: новая редакция'
        content.text = 'Обновлённый материал.'
        content.text_uz = 'Yangilangan material.'
        content.save()
        url = reverse('lesson', args=['functions'])
        self.assertContains(self.client.get(url), content.text)
        self.assertContains(self.client.get(reverse('learning')), content.title)
        self.assertEqual(len(self.client.get(url).context['quiz_fields']), 1)
        progress.refresh_from_db()
        self.assertTrue(progress.completed)
        self.assertEqual(progress.code, 'My private draft')
        self.assertEqual(progress.quiz_score, 100)
        self.student.profile.language = 'uz'
        self.student.profile.save()
        self.assertContains(self.client.get(url), content.text_uz)

    def test_admin_can_edit_content_but_not_change_its_identity(self):
        self.client.force_login(self.admin)
        content = LessonContent.objects.get(slug='functions')
        data = {field: getattr(content, field) for field in ('title', 'title_uz', 'summary', 'summary_uz', 'text', 'text_uz', 'hint', 'hint_uz', 'code', 'minutes')}
        data.update(title='Edited lesson', slug='forged-identity', _save='Save')
        url = reverse('admin:projects_lessoncontent_change', args=[content.pk])
        self.assertEqual(self.client.post(url, data).status_code, 302)
        content.refresh_from_db()
        self.assertEqual(content.slug, 'functions')
        self.assertEqual(content.title, 'Edited lesson')
        self.assertContains(self.client.get(reverse('content_admin')), url)
        self.client.force_login(self.student)
        self.assertEqual(self.client.post(url, data).status_code, 302)

    def test_minutes_are_validated(self):
        self.client.force_login(self.admin)
        content = LessonContent.objects.get(slug='functions')
        data = {field: getattr(content, field) for field in ('title', 'title_uz', 'summary', 'summary_uz', 'text', 'text_uz', 'hint', 'hint_uz', 'code', 'minutes')}
        data['minutes'] = 0
        response = self.client.post(reverse('admin:projects_lessoncontent_change', args=[content.pk]), data)
        self.assertEqual(response.status_code, 200)
        content.refresh_from_db()
        self.assertEqual(content.minutes, 12)
