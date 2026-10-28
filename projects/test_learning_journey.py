"""Exercise the complete student/reviewer journey using isolated test data."""
from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .catalog import LESSONS, QUESTIONS
from .lesson_checks import questions_for
from .models import LessonProgress, Notification, Submission, SubmissionDraft, TaskContent


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class LearningJourneyTests(TestCase):
    def journey(self, language):
        student = Client()
        response = student.post(reverse('register'), {
            'username': 'journey', 'email': 'journey@example.com',
            'password': 'Journey-study-123', 'password2': 'Journey-study-123', 'language': language,
        })
        self.assertRedirects(response, reverse('onboarding'))
        user = User.objects.get(username='journey')
        self.assertEqual(user.profile.language, language)
        self.assertRedirects(student.post(reverse('onboarding'), {
            'experience': 'basics', 'hours': '5-10',
        }), reverse('diagnostic'))
        student.post(reverse('diagnostic'), {f'q{i}': q['correct'] for i, q in enumerate(QUESTIONS)})
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.diagnostic_score, 100)

        for lesson in LESSONS:
            url = reverse('lesson', args=[lesson['slug']])
            student.post(url, {'action': 'complete', 'code': 'Personal notes'})
            answers = {f'answer_{i}': q['correct'] for i, q in enumerate(questions_for(lesson['slug']))}
            student.post(url, {'action': 'check', **answers})
        self.assertEqual(LessonProgress.objects.filter(user=user, completed=True, quiz_score=100).count(), len(LESSONS))
        self.assertTrue(student.get(reverse('learning')).context['all_completed'])

        url = reverse('submit', args=['orders'])
        student.post(url, {'action': 'draft', 'description': 'Work in progress'})
        self.assertTrue(SubmissionDraft.objects.filter(user=user).exists())
        task = TaskContent.objects.get(slug='orders')
        values = {'action': 'submit', 'repository': 'https://example.com/journey', 'commit': 'abc1234',
                  'description': 'Implemented and tested access', 'task_revision': str(task.revision),
                  'requirements_checked': 'on', 'tests_checked': 'on', 'secrets_checked': 'on'}
        student.post(url, values)
        first = Submission.objects.get(user=user)
        self.assertFalse(SubmissionDraft.objects.filter(user=user).exists())
        reviewer = User.objects.create_user('reviewer', password='test', is_staff=True)
        reviewer_client = Client()
        reviewer_client.force_login(reviewer)
        first.reviewer = reviewer
        first.save(update_fields=['reviewer'])
        reviewer_client.post(reverse('reviewer'), {
            'submission': first.pk, 'status': 'changes', 'score': 40, 'feedback': 'Add an access test',
        })
        first.refresh_from_db()
        self.assertEqual(first.status, 'changes')
        student.post(reverse('discussion', args=[first.pk]), {'body': 'I will add the test'})
        self.assertTrue(Notification.objects.filter(user=reviewer).exists())
        student.post(url, {**values, 'description': 'Added access test', 'commit': 'def5678'})
        latest = Submission.objects.filter(user=user).latest('pk')
        latest.reviewer = reviewer
        latest.save(update_fields=['reviewer'])
        reviewer_client.post(reverse('reviewer'), {
            'submission': latest.pk, 'status': 'done', 'score': 100, 'feedback': 'All criteria met',
        })
        payload = student.get(reverse('report'), {'format': 'json'}).json()
        self.assertEqual(payload['completed_lessons'], len(LESSONS))
        self.assertEqual(payload['accepted_tasks'], 1)
        self.assertEqual(len(payload['lesson_checks']), len(LESSONS))
        self.assertEqual(len(payload['submissions']), 2)
        self.assertEqual(payload['latest_submissions'][0]['id'], latest.pk)
        markdown = student.get(reverse('report'), {'format': 'markdown'})
        for expected in ('Added access test', 'def5678', 'All criteria met', task.requirements[0], 'https://example.com/journey'):
            self.assertContains(markdown, expected)
        notification = Notification.objects.filter(user=user, url=reverse('review_result', args=[latest.pk])).latest('pk')
        self.assertRedirects(student.post(reverse('notification_read', args=[notification.pk]), {'action': 'open'}), notification.url)
        notification.refresh_from_db()
        self.assertTrue(notification.read)

    def test_russian_student_finishes_course_and_receives_review(self):
        self.journey('ru')

    def test_uzbek_student_finishes_course_and_receives_review(self):
        self.journey('uz')
