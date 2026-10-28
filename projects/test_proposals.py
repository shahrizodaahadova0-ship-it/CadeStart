from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import ChangeProposal, Notification


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ProposalTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user('student', password='test')
        self.other = User.objects.create_user('other', password='test', is_staff=True)
        self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'test')
        self.proposal = ChangeProposal.objects.create(user=self.student, hours=5, days=2, question='How should discounts combine?')
        self.url = reverse('admin:projects_changeproposal_change', args=[self.proposal.pk])

    def test_admin_decision_requires_feedback_and_notifies_once(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url, {'status': 'approved', 'feedback': '', '_save': 'Save'})
        self.assertEqual(response.status_code, 200)
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, 'pending')
        self.assertFalse(Notification.objects.exists())
        data = {'status': 'approved', 'feedback': 'Agreed. Add tests for expired codes.', '_save': 'Save'}
        self.assertEqual(self.client.post(self.url, data).status_code, 302)
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.reviewed_by, self.admin)
        self.assertIsNotNone(self.proposal.reviewed_at)
        self.assertEqual(Notification.objects.get().user, self.student)
        self.client.post(self.url, data)
        self.assertEqual(Notification.objects.count(), 1)
        self.client.force_login(self.student)
        response = self.client.get(reverse('scenario'))
        self.assertContains(response, data['feedback'])
        self.assertContains(response, 'Согласовано')

    def test_unprivileged_staff_cannot_decide_or_read_student_proposal(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.client.post(self.url, {'status': 'approved', 'feedback': 'Unauthorized'}).status_code, 403)
        self.assertNotContains(self.client.get(reverse('scenario')), self.proposal.question)
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, 'pending')

    def test_student_cannot_forge_decision_when_submitting(self):
        self.client.force_login(self.student)
        self.client.post(reverse('scenario'), {'hours': 3, 'days': 1, 'question': 'New estimate', 'status': 'approved', 'reviewed_by': self.admin.pk})
        proposal = ChangeProposal.objects.get(question='New estimate')
        self.assertEqual(proposal.status, 'pending')
        self.assertIsNone(proposal.reviewed_by)
