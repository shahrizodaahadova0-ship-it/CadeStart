from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import ChangeProposal, Notification, Submission


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class AssignmentTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user('student', password='test')
        self.reviewer = User.objects.create_user('reviewer', password='test', is_staff=True)
        self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'test')
        self.entry = Submission.objects.create(user=self.student, task='orders', repository='https://example.com/', description='Original solution')
        self.url = reverse('admin:projects_submission_change', args=[self.entry.pk])
        self.client.force_login(self.admin)

    def data(self, **changes):
        values = {'reviewer': self.reviewer.pk, 'status': 'review', 'feedback': '', 'score': '', '_save': 'Save'}
        values.update(changes)
        return values

    def test_assignment_notifies_reviewer_once_and_preserves_student_content(self):
        self.assertEqual(self.client.post(self.url, self.data(description='Forged edit')).status_code, 302)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.reviewer, self.reviewer)
        self.assertEqual(self.entry.description, 'Original solution')
        self.assertEqual(Notification.objects.get().user, self.reviewer)
        self.client.post(self.url, self.data())
        self.assertEqual(Notification.objects.count(), 1)
        self.client.force_login(self.reviewer)
        self.assertContains(self.client.get(reverse('reviewer')), 'Original solution')

    def test_nonstaff_inactive_and_self_reviewers_are_rejected(self):
        inactive = User.objects.create_user('inactive', password='test', is_staff=True, is_active=False)
        self.student.is_staff = True
        self.student.save()
        nonstaff = User.objects.create_user('nonstaff', password='test')
        for user in (inactive, self.student, nonstaff):
            self.assertEqual(self.client.post(self.url, self.data(reviewer=user.pk)).status_code, 200)
            self.entry.refresh_from_db()
            self.assertIsNone(self.entry.reviewer)
        self.assertFalse(Notification.objects.exists())

    def test_admin_review_requires_feedback_and_notifies_student(self):
        response = self.client.post(self.url, self.data(status='changes'))
        self.assertEqual(response.status_code, 200)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.status, 'review')
        self.client.post(self.url, self.data(status='changes', feedback='Add permission tests.', score=70))
        self.assertEqual(Notification.objects.filter(user=self.student).count(), 1)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.status, 'changes')

    def test_management_counts_are_restricted_to_authorized_users(self):
        ChangeProposal.objects.create(user=self.student, hours=2, days=1)
        response = self.client.get(reverse('content_admin'))
        self.assertEqual(response.context['unassigned_count'], 1)
        self.assertEqual(response.context['pending_proposal_count'], 1)
        self.assertContains(response, '?status__exact=review')
        self.client.force_login(self.reviewer)
        response = self.client.get(reverse('content_admin'))
        self.assertFalse(response.context['can_manage_submissions'])
        self.assertIsNone(response.context['unassigned_count'])
        self.assertIsNone(response.context['pending_proposal_count'])
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(reverse('content_admin')).status_code, 302)
