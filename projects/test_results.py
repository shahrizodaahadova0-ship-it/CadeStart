from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Submission, SubmissionDraft


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ResultsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('student', password='test')
        self.other = User.objects.create_user('other', password='test')
        self.client.force_login(self.user)

    def submission(self, task, status, user=None):
        return Submission.objects.create(user=user or self.user, task=task, status=status,
                                         repository='https://example.com/', description='Test')

    def test_summary_uses_latest_version_even_when_timestamps_tie(self):
        self.submission('orders', 'done')
        latest = self.submission('orders', 'changes')
        self.submission('cart', 'done')
        self.submission('orders', 'done', user=self.other)
        Submission.objects.update(created_at=timezone.now())
        response = self.client.get(reverse('results'))
        self.assertEqual(response.context['accepted'], 1)
        self.assertEqual(response.context['submission_count'], 3)
        self.assertEqual(response.context['submissions'].paginator.count, 2)
        self.assertIn(latest, response.context['submissions'])
        self.assertEqual(self.client.get(reverse('task', args=['orders'])).context['latest'], latest)
        self.assertEqual(self.client.get(reverse('dashboard')).context['accepted'], 1)
        filtered = self.client.get(reverse('results'), {'status': 'done'})
        self.assertEqual(filtered.context['submissions'].paginator.count, 1)
        history = self.client.get(reverse('results'), {'view': 'history'})
        self.assertEqual(history.context['submissions'].paginator.count, 3)

    def test_exports_keep_all_attempts_and_separate_latest_versions(self):
        old = self.submission('orders', 'changes')
        current = self.submission('orders', 'done')
        private = self.submission('cart', 'done', user=self.other)
        payload = self.client.get(reverse('report'), {'format': 'json'}).json()
        self.assertEqual(payload['accepted_tasks'], 1)
        self.assertEqual([entry['id'] for entry in payload['latest_submissions']], [current.pk])
        self.assertEqual({entry['id'] for entry in payload['submissions']}, {old.pk, current.pk})
        self.assertNotIn(private.pk, [entry['id'] for entry in payload['submissions']])
        self.assertIn('created_at', payload['submissions'][0])
        self.assertContains(self.client.get(reverse('report'), {'format': 'markdown'}), 'История всех отправок')

    def test_attempt_history_pagination_keeps_filters(self):
        for _ in range(12):
            self.submission('orders', 'review')
        response = self.client.get(reverse('results'), {'view': 'history', 'status': 'review', 'page': 2})
        self.assertEqual(len(response.context['submissions']), 2)
        self.assertContains(response, 'view=history')
        self.assertContains(response, 'status=review')

    def test_draft_moves_unsubmitted_task_into_work_and_discard_returns_it(self):
        draft = SubmissionDraft.objects.create(user=self.user, task='orders', description='Working')
        response = self.client.get(reverse('kanban'), {'status': 'inprogress'})
        self.assertEqual(response.context['found'], 1)
        self.assertEqual(response.context['columns'][0]['tasks'][0]['slug'], 'orders')
        self.submission('orders', 'review')
        self.assertEqual(self.client.get(reverse('kanban'), {'status': 'inprogress'}).context['found'], 0)
        self.assertEqual(self.client.get(reverse('kanban'), {'status': 'review'}).context['found'], 1)
        Submission.objects.filter(user=self.user).delete()
        draft.delete()
        self.assertEqual(self.client.get(reverse('kanban'), {'status': 'todo'}).context['found'], 5)
