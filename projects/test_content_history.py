from django.contrib.auth.models import Permission, User
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.contrib import admin

from .models import ContentEdit, LessonContent, TaskContent


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ContentHistoryTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'test')
        self.client.force_login(self.admin)

    def test_lesson_changes_capture_both_versions_and_author(self):
        lesson = LessonContent.objects.get(slug='functions')
        values = {field: getattr(lesson, field) for field in ('title', 'title_uz', 'summary', 'summary_uz', 'text', 'text_uz', 'hint', 'hint_uz', 'code', 'minutes')}
        original = lesson.text
        values.update(text='Revised teaching material.', _save='Save')
        url = reverse('admin:projects_lessoncontent_change', args=[lesson.pk])
        self.assertEqual(self.client.post(url, values).status_code, 302)
        entry = ContentEdit.objects.get()
        self.assertEqual(entry.author, self.admin)
        self.assertEqual(entry.before['text'], original)
        self.assertEqual(entry.after['text'], values['text'])
        self.assertEqual(entry.changed_fields, ['text'])
        self.client.post(url, values)
        self.assertEqual(ContentEdit.objects.count(), 1)

    def test_task_history_records_revision_and_history_cannot_be_edited(self):
        task = TaskContent.objects.get(slug='orders')
        values = {field: getattr(task, field) for field in ('title', 'title_uz', 'description', 'description_uz', 'tag', 'priority')}
        values.update(requirements='\n'.join(task.requirements), requirements_uz='\n'.join(task.requirements_uz), title='Revised order task', _save='Save')
        url = reverse('admin:projects_taskcontent_change', args=[task.pk])
        self.assertEqual(self.client.post(url, values).status_code, 302)
        entry = ContentEdit.objects.get()
        self.assertEqual(entry.before['revision'], 1)
        self.assertEqual(entry.after['revision'], 2)
        history_url = reverse('admin:projects_contentedit_change', args=[entry.pk])
        self.assertEqual(self.client.get(history_url).status_code, 200)
        self.assertEqual(self.client.post(history_url, {'slug': 'forged'}).status_code, 403)
        entry.refresh_from_db()
        self.assertEqual(entry.slug, 'orders')

    def test_editor_can_only_read_history_for_permitted_materials(self):
        editor = User.objects.create_user('editor', password='test', is_staff=True)
        editor.user_permissions.add(Permission.objects.get(codename='change_lessoncontent'))
        ContentEdit.objects.create(kind='lesson', slug='functions', author=self.admin, before={}, after={}, changed_fields=[])
        ContentEdit.objects.create(kind='task', slug='private-task', author=self.admin, before={}, after={}, changed_fields=[])
        request = RequestFactory().get('/')
        request.user = editor
        model_admin = admin.site._registry[ContentEdit]
        self.assertEqual(list(model_admin.get_queryset(request).values_list('kind', flat=True)), ['lesson'])
        self.client.force_login(editor)
        response = self.client.get(reverse('admin:projects_contentedit_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'private-task')

    def test_restore_creates_new_task_revision_and_keeps_history_immutable(self):
        task = TaskContent.objects.get(slug='orders')
        fields = admin.site._registry[TaskContent].audit_fields
        before = {field: getattr(task, field) for field in fields}
        original_title = task.title
        task.title = 'New title'
        task.save()
        entry = ContentEdit.objects.create(kind='task', slug=task.slug, author=self.admin, before=before,
                                           after={field: getattr(task, field) for field in fields}, changed_fields=['title'])
        url = reverse('admin:projects_contentedit_restore', args=[entry.pk])
        response = self.client.get(url)
        token = response.context['restore_token']
        self.assertEqual(self.client.post(url, {'token': token}).status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.title, original_title)
        self.assertEqual(task.revision, 3)
        self.assertEqual(ContentEdit.objects.count(), 2)
        entry.refresh_from_db()
        self.assertEqual(entry.after['title'], 'New title')

    def test_stale_confirmation_does_not_overwrite_newer_lesson_edit(self):
        lesson = LessonContent.objects.get(slug='functions')
        fields = admin.site._registry[LessonContent].audit_fields
        before = {field: getattr(lesson, field) for field in fields}
        entry = ContentEdit.objects.create(kind='lesson', slug=lesson.slug, author=self.admin,
                                           before=before, after=before, changed_fields=[])
        url = reverse('admin:projects_contentedit_restore', args=[entry.pk])
        token = self.client.get(url).context['restore_token']
        lesson.text = 'A newer edit that must survive.'
        lesson.save()
        response = self.client.post(url, {'token': token})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['restore_errors'])
        lesson.refresh_from_db()
        self.assertEqual(lesson.text, 'A newer edit that must survive.')

    def test_view_permission_does_not_allow_restore(self):
        viewer = User.objects.create_user('viewer', password='test', is_staff=True)
        viewer.user_permissions.add(Permission.objects.get(codename='view_lessoncontent'))
        entry = ContentEdit.objects.create(kind='lesson', slug='functions', author=self.admin,
                                           before={}, after={}, changed_fields=[])
        self.client.force_login(viewer)
        history_url = reverse('admin:projects_contentedit_change', args=[entry.pk])
        self.assertEqual(self.client.get(history_url).status_code, 200)
        url = reverse('admin:projects_contentedit_restore', args=[entry.pk])
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, {'token': 'forged'}).status_code, 403)
