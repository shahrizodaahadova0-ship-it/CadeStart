from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Submission, SubmissionDraft, TaskContent
from .forms import TaskContentForm


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class TaskContentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('student', password='test')
        self.client.force_login(self.user)
        self.task = TaskContent.objects.get(slug='orders')
        self.url = reverse('submit', args=['orders'])

    def values(self, **extra):
        values = {'task_revision': str(self.task.revision), 'repository': 'https://example.com/shop',
                  'description': 'Implemented and tested', 'requirements_checked': 'on',
                  'tests_checked': 'on', 'secrets_checked': 'on'}
        values.update(extra)
        return values

    def test_snapshot_survives_later_edits_and_revision_changes_only_for_changes(self):
        self.client.post(self.url, self.values())
        entry = Submission.objects.get()
        original_title = self.task.title
        self.task.title = 'Новая версия заказа'
        self.task.save()
        self.assertEqual(self.task.revision, 2)
        self.task.save()
        self.assertEqual(self.task.revision, 2)
        entry.refresh_from_db()
        self.assertEqual(entry.task_title, original_title)
        self.assertEqual(entry.task_snapshot['revision'], 1)
        response = self.client.get(reverse('review_result', args=[entry.pk]))
        self.assertContains(response, original_title)
        self.assertNotContains(response, self.task.title)
        self.assertContains(self.client.get(reverse('task', args=['orders'])), self.task.title)
        self.assertContains(self.client.get(reverse('task', args=['orders'])), 'Прежняя проверка сохранена')

    def test_stale_submission_preserves_draft_and_does_not_create_review(self):
        SubmissionDraft.objects.create(user=self.user, task='orders', description='Keep my draft')
        old_values = self.values()
        self.task.description += ' Updated.'
        self.task.save()
        response = self.client.post(self.url, old_values)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].non_field_errors())
        self.assertFalse(Submission.objects.exists())
        self.assertTrue(SubmissionDraft.objects.filter(user=self.user).exists())
        self.client.post(self.url, self.values())
        self.assertEqual(Submission.objects.get().task_snapshot['revision'], 2)

    def test_checklists_are_edited_as_lines_with_matching_translations(self):
        values = {field: getattr(self.task, field) for field in ('title', 'title_uz', 'description', 'description_uz', 'tag', 'priority')}
        values.update(requirements='First criterion\nSecond criterion', requirements_uz='Birinchi mezon')
        form = TaskContentForm(values, instance=self.task)
        self.assertFalse(form.is_valid())
        self.assertIn('requirements_uz', form.errors)
        values['requirements_uz'] += '\nIkkinchi mezon'
        form = TaskContentForm(values, instance=self.task)
        self.assertTrue(form.is_valid(), form.errors)
        saved = form.save()
        self.assertEqual(saved.requirements, ['First criterion', 'Second criterion'])

    def test_partial_update_keeps_persisted_revision_consistent(self):
        self.task.title = 'Updated title'
        self.task.save(update_fields=['title'])
        self.task.refresh_from_db()
        self.assertEqual(self.task.revision, 2)

    def test_unknown_action_does_not_submit_or_delete_draft(self):
        draft = SubmissionDraft.objects.create(user=self.user, task='orders', description='Keep draft')
        response = self.client.post(self.url, self.values(action='unexpected'))
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Submission.objects.exists())
        draft.refresh_from_db()
        self.assertEqual(draft.description, 'Keep draft')
