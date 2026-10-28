from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Notification, Submission, SubmissionComment


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class DiscussionTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user('student', password='test')
        self.reviewer = User.objects.create_user('reviewer', password='test', is_staff=True)
        self.outsider = User.objects.create_user('outsider', password='test', is_staff=True)
        self.submission = Submission.objects.create(user=self.student, reviewer=self.reviewer,
                                                    task='orders', repository='https://example.com/', description='Test')
        self.url = reverse('discussion', args=[self.submission.pk])

    def test_only_owner_and_assigned_staff_can_read_and_comment(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.post(self.url, {'body': 'Unauthorized'}).status_code, 404)
        self.assertFalse(SubmissionComment.objects.exists())
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.client.force_login(self.reviewer)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_replies_notify_the_other_participant_without_changing_review(self):
        self.client.force_login(self.student)
        self.assertRedirects(self.client.post(self.url, {'body': 'How should I test access?', 'author': self.outsider.pk}), self.url)
        comment = SubmissionComment.objects.get()
        self.assertEqual(comment.author, self.student)
        self.assertEqual(Notification.objects.get().user, self.reviewer)
        self.client.force_login(self.reviewer)
        self.client.post(self.url, {'body': '<script>alert(1)</script> Test another user.'})
        self.assertEqual(Notification.objects.filter(user=self.student).count(), 1)
        response = self.client.get(self.url)
        self.assertContains(response, '&lt;script&gt;')
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, 'review')
        self.assertIsNone(self.submission.score)

    def test_invalid_comment_and_reassignment(self):
        self.client.force_login(self.student)
        response = self.client.post(self.url, {'body': '   '})
        self.assertIn('body', response.context['form'].errors)
        self.assertFalse(SubmissionComment.objects.exists())
        self.submission.reviewer = self.outsider
        self.submission.save(update_fields=['reviewer'])
        self.client.force_login(self.reviewer)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get(self.url).status_code, 200)
