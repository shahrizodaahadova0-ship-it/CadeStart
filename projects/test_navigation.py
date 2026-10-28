from django.contrib.auth.models import User, Permission
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class NavigationTests(TestCase):
    def setUp(self):
        self.reviewer = User.objects.create_user('reviewer', password='test', is_staff=True)
        self.client.force_login(self.reviewer)

    def test_reviewer_has_no_dead_end_admin_edit_links(self):
        response = self.client.get(reverse('content_admin'))
        for url in (reverse('admin:index'), reverse('admin:projects_submission_changelist'), reverse('admin:projects_project_changelist')):
            self.assertNotContains(response, f'href="{url}"')
        self.assertContains(response, reverse('reviewer'))
        self.assertContains(response, reverse('lesson', args=['functions']))

    def test_scoped_editor_sees_only_permitted_admin_actions(self):
        self.reviewer.user_permissions.add(Permission.objects.get(codename='change_project', content_type__app_label='projects'))
        response = self.client.get(reverse('content_admin'))
        self.assertContains(response, reverse('admin:projects_project_changelist'))
        self.assertNotContains(response, reverse('admin:projects_submission_changelist'))

    def test_student_has_no_staff_menu_and_materials_remain_accessible(self):
        student = User.objects.create_user('student', password='test')
        self.client.force_login(student)
        response = self.client.get(reverse('dashboard'))
        self.assertNotContains(response, f'href="{reverse("content_admin")}"')
        self.assertNotContains(response, f'href="{reverse("reviewer")}"')
        self.assertEqual(self.client.get(reverse('learning')).status_code, 200)
        self.assertEqual(self.client.get(reverse('lesson', args=['functions'])).status_code, 200)
