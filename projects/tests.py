from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Profile, Project
from .models import LessonProgress, Submission, Notification, SubmissionDraft
from .catalog import QUESTIONS
from django.core import mail, signing
from django.test import override_settings


class AccountTests(TestCase):
    def test_registration_creates_one_profile_and_logs_in(self):
        response = self.client.post(reverse('register'), {
            'username': 'student', 'password': 'Learn-Code-123',
            'password2': 'Learn-Code-123', 'language': 'uz',
        })
        self.assertRedirects(response, reverse('onboarding'))
        user = User.objects.get(username='student')
        self.assertEqual(Profile.objects.filter(user=user).count(), 1)
        self.assertEqual(user.profile.language, 'uz')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_anonymous_profile_redirects_to_login(self):
        self.assertRedirects(
            self.client.get(reverse('profile')), '/login/?next=/profile/'
        )

    def test_language_post_updates_session_and_template(self):
        self.client.post(reverse('language_choice'), {'language': 'uz'})
        response = self.client.get(reverse('home'))
        self.assertEqual(response.context['current_language'], 'uz')
        self.assertContains(response, 'Qidirish')

    def test_language_post_updates_existing_profile(self):
        user = User.objects.create_user('student', password='Learn-Code-123')
        self.client.force_login(user)
        self.client.post(reverse('language_choice'), {'language': 'uz'})
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.language, 'uz')

    def test_language_rejects_external_redirect_and_unknown_language(self):
        response = self.client.post(
            reverse('language_choice'), {'language': 'unknown'},
            HTTP_REFERER='https://example.com/',
        )
        self.assertRedirects(response, '/')
        self.assertEqual(self.client.session['language'], 'ru')


class ProjectSearchTests(TestCase):
    def test_search_matches_title_description_and_technologies(self):
        for field in ('title', 'description', 'technologies'):
            values = dict(title='Example', description='Practice', technologies='HTML',
                          category='python', level='beginner')
            values[field] = 'Python tutorial'
            Project.objects.create(**values)
        Project.objects.create(title='Other', description='Other', technologies='CSS',
                               category='web', level='beginner')
        response = self.client.get(reverse('home'), {'q': '  python  '})
        self.assertEqual(response.context['projects'].count(), 3)
        self.assertEqual(response.context['query'], 'python')

    def test_no_matches_returns_empty_catalog(self):
        response = self.client.get(reverse('home'), {'q': 'missing'})
        self.assertEqual(list(response.context['projects']), [])


class PlatformTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('learner', 'learner@example.com', 'Study-Platform-123')
        self.other = User.objects.create_user('other', password='Study-Platform-123')
        self.client.force_login(self.user)

    def test_all_student_pages_render_in_both_languages(self):
        routes = ['home', 'dashboard', 'onboarding', 'diagnostic', 'diagnostic_result',
                  'learning', 'company', 'kanban', 'mentor', 'manager', 'documents', 'team',
                  'scenario', 'notifications', 'results', 'report', 'profile', 'states', 'email_verification']
        for language in ('ru', 'uz'):
            self.user.profile.language = language
            self.user.profile.save()
            for route in routes:
                with self.subTest(route=route, language=language):
                    self.assertEqual(self.client.get(reverse(route)).status_code, 200)
            for route, slug in [('lesson', 'functions'), ('task', 'orders'), ('submit', 'orders')]:
                with self.subTest(route=route, language=language):
                    self.assertEqual(self.client.get(reverse(route, args=[slug])).status_code, 200)

    def test_diagnostic_is_scored_on_server(self):
        answers = {f'q{i}': q['correct'] for i, q in enumerate(QUESTIONS)}
        response = self.client.post(reverse('diagnostic'), answers)
        self.assertRedirects(response, reverse('diagnostic_result'))
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.diagnostic_score, 100)

    def test_lesson_draft_and_completion_are_isolated(self):
        url = reverse('lesson', args=['functions'])
        self.client.post(url, {'code': 'return sum(prices)', 'action': 'save'})
        progress = LessonProgress.objects.get(user=self.user, lesson='functions')
        self.assertFalse(progress.completed)
        self.client.post(url, {'code': 'return sum(prices)', 'action': 'complete'})
        progress.refresh_from_db()
        self.assertTrue(progress.completed)
        self.client.force_login(self.other)
        response = self.client.get(url)
        self.assertNotContains(response, 'return sum(prices)')

    def test_submission_requires_checklist_and_creates_notification(self):
        url = reverse('submit', args=['orders'])
        values = {'repository': 'https://github.com/student/shop', 'commit': 'abc1234', 'description': 'Added API and tested access.'}
        self.client.post(url, values)
        self.assertFalse(Submission.objects.exists())
        values.update(requirements_checked='on', tests_checked='on', secrets_checked='on', task_revision='1')
        response = self.client.post(url, values)
        submission = Submission.objects.get(user=self.user)
        self.assertRedirects(response, reverse('review_result', args=[submission.pk]))
        self.assertEqual(Notification.objects.filter(user=self.user).count(), 1)
        self.assertContains(self.client.get(reverse('kanban')), 'На проверке')
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse('review_result', args=[submission.pk])).status_code, 404)

    def test_solution_draft_accepts_partial_fields_without_submitting(self):
        url = reverse('submit', args=['orders'])
        response = self.client.post(url, {'action': 'draft', 'repository': 'https://github.com/',
                                         'commit': 'unfinished', 'description': 'Working on access tests.'})
        self.assertRedirects(response, url)
        self.assertFalse(Submission.objects.exists())
        self.assertFalse(Notification.objects.exists())
        draft = SubmissionDraft.objects.get(user=self.user, task='orders')
        self.assertEqual(draft.commit, 'unfinished')
        self.assertEqual(self.client.get(url).context['form'].initial['description'], draft.description)
        self.assertContains(self.client.get(reverse('kanban')), 'Есть черновик')
        self.client.force_login(self.other)
        self.assertIsNone(self.client.get(url).context['draft'])
        self.client.post(url, {'action': 'discard'})
        self.assertTrue(SubmissionDraft.objects.filter(pk=draft.pk).exists())

    def test_final_submission_validates_and_clears_only_its_draft(self):
        url = reverse('submit', args=['orders'])
        self.client.post(url, {'action': 'draft', 'description': 'Draft'})
        self.client.post(reverse('submit', args=['cart']), {'action': 'draft', 'description': 'Other draft'})
        self.client.post(url, {'action': 'submit', 'description': 'Missing checklist'})
        self.assertTrue(SubmissionDraft.objects.filter(user=self.user, task='orders').exists())
        self.assertFalse(Submission.objects.exists())
        values = {'action': 'submit', 'repository': 'https://github.com/student/shop',
                  'description': 'Implemented and tested.', 'requirements_checked': 'on',
                  'tests_checked': 'on', 'secrets_checked': 'on', 'task_revision': '1'}
        self.client.post(url, values)
        self.assertEqual(Submission.objects.filter(user=self.user).count(), 1)
        self.assertFalse(SubmissionDraft.objects.filter(user=self.user, task='orders').exists())
        self.assertTrue(SubmissionDraft.objects.filter(user=self.user, task='cart').exists())

    def test_empty_draft_is_preserved_and_can_be_discarded(self):
        url = reverse('submit', args=['orders'])
        self.client.post(url, {'action': 'draft', 'description': 'Initial text'})
        self.client.post(url, {'action': 'draft', 'description': ''})
        self.assertEqual(SubmissionDraft.objects.get(user=self.user).description, '')
        self.client.post(url, {'action': 'discard'})
        self.assertFalse(SubmissionDraft.objects.filter(user=self.user).exists())

    def test_notification_read_only_affects_current_user(self):
        own = Notification.objects.create(user=self.user, title='Own')
        other = Notification.objects.create(user=self.other, title='Other')
        self.client.post(reverse('notifications'))
        own.refresh_from_db()
        other.refresh_from_db()
        self.assertTrue(own.read)
        self.assertFalse(other.read)

    def test_single_notification_read_and_open_are_private_post_actions(self):
        own = Notification.objects.create(user=self.user, title='Own', url='/learning/')
        other = Notification.objects.create(user=self.other, title='Private')
        url = reverse('notification_read', args=[own.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.get(reverse('dashboard')).context['unread_notifications'], 1)
        self.assertRedirects(self.client.post(url, {'action': 'open'}), '/learning/')
        own.refresh_from_db()
        self.assertTrue(own.read)
        self.assertEqual(self.client.get(reverse('dashboard')).context['unread_notifications'], 0)
        self.assertEqual(self.client.post(reverse('notification_read', args=[other.pk])).status_code, 404)
        other.refresh_from_db()
        self.assertFalse(other.read)

    def test_notification_open_rejects_external_redirects(self):
        entry = Notification.objects.create(user=self.user, title='External', url='https://example.com/')
        self.assertRedirects(self.client.post(reverse('notification_read', args=[entry.pk]),
                                             {'action': 'open'}), reverse('notifications'))

    def test_notification_pagination_and_unread_filter(self):
        Notification.objects.bulk_create([
            Notification(user=self.user, title=f'Notice {index}', read=index == 0)
            for index in range(18)
        ])
        response = self.client.get(reverse('notifications'), {'filter': 'unread'})
        self.assertEqual(len(response.context['notifications']), 15)
        self.assertEqual(response.context['notifications'].paginator.count, 17)
        response = self.client.get(reverse('notifications'), {'filter': 'unread', 'page': 2})
        self.assertEqual(len(response.context['notifications']), 2)
        self.assertEqual(response.context['unread_notifications'], 17)

    def test_report_export_contains_only_current_user(self):
        Submission.objects.create(user=self.other, task='hidden-task', repository='https://example.com/', description='Private')
        response = self.client.get(reverse('report'), {'format': 'json'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['student'], 'learner')
        self.assertEqual(response.json()['submissions'], [])
        self.assertNotContains(self.client.get(reverse('report')), 'hidden-task')

    def test_profile_validates_timezone_and_updates_preferences(self):
        values = {'first_name': 'Abror', 'email': self.user.email, 'language': 'uz', 'timezone': 'bad/zone', 'weekly_hours': '5-10'}
        self.client.post(reverse('profile'), values)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, '')
        values['timezone'] = 'Asia/Tashkent'
        self.assertRedirects(self.client.post(reverse('profile'), values), reverse('profile'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Abror')
        self.assertEqual(self.user.profile.language, 'uz')

    def test_reviewer_is_limited_to_assigned_submissions(self):
        self.user.is_staff = True
        self.user.save()
        own = Submission.objects.create(user=self.other, reviewer=self.user, task='orders', repository='https://example.com/', description='Assigned')
        hidden = Submission.objects.create(user=self.other, task='cart', repository='https://example.com/', description='Unassigned secret')
        response = self.client.get(reverse('reviewer'))
        self.assertContains(response, 'Assigned')
        self.assertNotContains(response, 'Unassigned secret')
        self.client.post(reverse('reviewer') + f'?submission={hidden.pk}', {'status': 'done', 'score': 90, 'feedback': 'No access'})
        hidden.refresh_from_db()
        self.assertEqual(hidden.status, 'review')
        self.client.post(reverse('reviewer') + f'?submission={own.pk}', {'status': 'done', 'score': 90, 'feedback': 'Good tests'})
        own.refresh_from_db()
        self.assertEqual(own.status, 'done')
        self.assertTrue(Notification.objects.filter(user=self.other).exists())
        self.assertEqual(self.client.get(reverse('content_admin')).status_code, 200)

    def test_nonstaff_cannot_open_management(self):
        for route in ('reviewer', 'content_admin'):
            self.assertEqual(self.client.get(reverse(route)).status_code, 302)

    @override_settings(MAILERS={'default': {'BACKEND': 'django.core.mail.backends.locmem.EmailBackend'}})
    def test_email_verification_and_reset_send_real_tokens(self):
        self.client.post(reverse('email_verification'))
        self.assertEqual(len(mail.outbox), 1)
        token = signing.dumps({'user': self.user.pk, 'email': self.user.email}, salt='codestart-email')
        self.client.get(reverse('verify_email', args=[token]))
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.email_verified)
        self.client.post(reverse('password_reset'), {'email': self.user.email})
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn('/password/new/', mail.outbox[-1].body)

    def test_logout_requires_post(self):
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        self.assertRedirects(self.client.post(reverse('logout')), reverse('home'))

    def test_password_change_checks_old_password_and_keeps_current_session(self):
        url = reverse('password_change')
        new = 'New-Secure-Account-874!'
        data = {'old_password': 'incorrect', 'new_password1': new, 'new_password2': new}
        response = self.client.post(url, data)
        self.assertIn('old_password', response.context['form'].errors)
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password(new))
        data['old_password'] = 'Study-Platform-123'
        self.assertRedirects(self.client.post(url, data), reverse('password_change_done'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new))
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 200)
        from django.test import Client
        old_session = Client()
        self.assertFalse(old_session.login(username=self.user.username, password='Study-Platform-123'))
        self.assertTrue(old_session.login(username=self.user.username, password=new))

    def test_password_change_requires_login_and_renders_both_languages(self):
        for language in ('ru', 'uz'):
            self.user.profile.language = language
            self.user.profile.save()
            self.assertEqual(self.client.get(reverse('password_change')).status_code, 200)
            self.assertContains(self.client.get(reverse('profile')), reverse('password_change'))
        self.client.logout()
        self.assertEqual(self.client.get(reverse('password_change')).status_code, 302)

    def test_diagnostic_can_resume_without_overwriting_previous_result(self):
        profile = self.user.profile
        profile.diagnostic_score = 75
        profile.save()
        response = self.client.post(reverse('diagnostic'), {
            'action': 'save', 'step': '4', 'q0': '1', 'q1': '2',
        })
        self.assertRedirects(response, reverse('dashboard'))
        profile.refresh_from_db()
        self.assertEqual(profile.diagnostic_score, 75)
        self.assertEqual(profile.diagnostic_draft['step'], 4)
        response = self.client.get(reverse('diagnostic'))
        self.assertEqual(len(response.context['questions']), 12)
        self.assertEqual(response.context['questions'][0]['selected'], '1')
        self.assertEqual(response.context['step'], 4)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse('diagnostic')).context['step'], 0)

    def test_diagnostic_recommends_first_weak_topic_and_clears_draft(self):
        answers = {f'q{i}': q['correct'] for i, q in enumerate(QUESTIONS)}
        answers['q1'] = 'skip'
        self.client.post(reverse('diagnostic'), {'action': 'save', **answers})
        self.client.post(reverse('diagnostic'), {'action': 'complete', **answers})
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.recommended_lesson, 'functions')
        self.assertEqual(self.user.profile.diagnostic_draft, {})
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.context['current']['slug'], 'functions')
        LessonProgress.objects.create(user=self.user, lesson='functions', completed=True)
        self.assertEqual(self.client.get(reverse('dashboard')).context['current']['slug'], 'basics')
        response = self.client.get(reverse('diagnostic_result'))
        self.assertContains(response, reverse('lesson', args=['functions']))
        topic = next(t for t in response.context['topic_results'] if t['slug'] == 'functions')
        self.assertEqual(topic['correct'], 0)

    def test_opening_lesson_does_not_create_progress_and_empty_draft_is_preserved(self):
        url = reverse('lesson', args=['functions'])
        self.client.get(url)
        self.assertFalse(LessonProgress.objects.filter(user=self.user).exists())
        self.client.post(url, {'action': 'save', 'code': ''})
        self.assertEqual(self.client.get(url).context['code'], '')

    def test_board_search_supports_id_and_both_languages(self):
        for query in ('shop-03', 'Создание заказа', 'Buyurtma yaratish'):
            response = self.client.get(reverse('kanban'), {'q': query})
            self.assertEqual(response.context['found'], 1)
            tasks = [task for column in response.context['columns'] for task in column['tasks']]
            self.assertEqual(tasks[0]['slug'], 'orders')
        response = self.client.get(reverse('kanban'), {'q': 'nonexistent'})
        self.assertEqual(response.context['found'], 0)
        self.assertContains(response, 'Задачи не найдены')

    def test_review_changes_require_actionable_feedback(self):
        self.user.is_staff = True
        self.user.save()
        entry = Submission.objects.create(user=self.other, reviewer=self.user, task='orders',
                                          repository='https://example.com/', description='Test solution')
        url = reverse('reviewer')
        data = {'submission': entry.pk, 'status': 'changes', 'feedback': '   ', 'score': 70}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('feedback', response.context['form'].errors)
        entry.refresh_from_db()
        self.assertEqual(entry.status, 'review')
        self.assertFalse(Notification.objects.filter(user=self.other).exists())
        data['feedback'] = 'Filter orders by request.user and add an access test.'
        self.assertEqual(self.client.post(url, data).status_code, 302)
        entry.refresh_from_db()
        self.assertEqual(entry.status, 'changes')
        self.assertEqual(Notification.objects.filter(user=self.other).count(), 1)
        self.client.post(url, data)
        self.assertEqual(Notification.objects.filter(user=self.other).count(), 1)

    def test_review_filters_preserve_assignment_permissions(self):
        self.user.is_staff = True
        self.user.save()
        entry = Submission.objects.create(user=self.other, reviewer=self.user, task='orders',
                                          repository='https://example.com/', description='Visible')
        hidden = Submission.objects.create(user=self.other, task='orders',
                                           repository='https://example.com/', description='Secret')
        response = self.client.get(reverse('reviewer'), {'q': 'other', 'status': 'review'})
        self.assertEqual(list(response.context['assigned']), [entry])
        self.assertEqual(response.context['counts']['review'], 1)
        self.assertContains(response, 'q=other')
        self.assertEqual(self.client.get(reverse('reviewer'), {'submission': hidden.pk}).status_code, 404)
        self.assertEqual(self.client.get(reverse('reviewer'), {'submission': '9' * 100}).status_code, 404)
        self.assertEqual(self.client.post(reverse('reviewer'), {'status': 'done'}).status_code, 400)

    def test_board_filters_latest_attempt_without_exposing_other_users(self):
        Submission.objects.create(user=self.user, task='orders', status='done',
                                  repository='https://example.com/', description='Old attempt')
        latest = Submission.objects.create(user=self.user, task='orders', status='review',
                                           repository='https://example.com/', description='Latest attempt')
        private = Submission.objects.create(user=self.other, task='orders', status='done',
                                            repository='https://example.com/', description='Private attempt')
        response = self.client.get(reverse('kanban'), {'status': 'review', 'q': 'SHOP-03'})
        self.assertEqual(response.context['found'], 1)
        self.assertEqual(len(response.context['columns']), 1)
        self.assertContains(response, reverse('review_result', args=[latest.pk]))
        self.assertNotContains(response, reverse('review_result', args=[private.pk]))
        self.assertEqual(self.client.get(reverse('kanban'), {'status': 'done'}).context['found'], 0)
        self.assertEqual(self.client.get(reverse('kanban'), {'status': 'todo'}).context['found'], 4)
        self.assertEqual(self.client.get(reverse('kanban'), {'status': 'unknown'}).context['found'], 5)
