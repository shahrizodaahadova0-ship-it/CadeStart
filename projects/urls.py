from django.urls import path
from django.contrib.auth import views as auth_views
from . import platform_views as platform

from .views import (
    home,
    project_detail,
    register_view,
    login_view,
    logout_view,
    profile_view,
    language_choice,
)

urlpatterns = [

    path(
        '',
        home,
        name='home'
    ),

    path(
        'language/',
        language_choice,
        name='language_choice'
    ),

    path(
        'project/<int:pk>/',
        project_detail,
        name='project_detail'
    ),

    path(
        'register/',
        register_view,
        name='register'
    ),

    path(
        'login/',
        login_view,
        name='login'
    ),

    path(
        'logout/',
        platform.logout_post,
        name='logout'
    ),

    path(
        'profile/',
        platform.settings_view,
        name='profile'
    ),
]

urlpatterns += [
    path('email/verify/', platform.email_verification, name='email_verification'),
    path('email/verify/<str:token>/', platform.verify_email, name='verify_email'),
    path('dashboard/', platform.dashboard, name='dashboard'),
    path('onboarding/', platform.onboarding, name='onboarding'),
    path('diagnostic/', platform.diagnostic, name='diagnostic'),
    path('diagnostic/result/', platform.diagnostic_result, name='diagnostic_result'),
    path('learning/', platform.learning, name='learning'),
    path('learning/<slug:slug>/', platform.lesson, name='lesson'),
    path('company/', platform.company, name='company'),
    path('company/tasks/', platform.kanban, name='kanban'),
    path('company/task/<slug:slug>/', platform.task_detail, name='task'),
    path('company/task/<slug:slug>/submit/', platform.submit, name='submit'),
    path('review/<int:pk>/', platform.review_result, name='review_result'),
    path('review/<int:pk>/discussion/', platform.discussion, name='discussion'),
    path('company/documents/', platform.documents, name='documents'),
    path('company/team/', platform.team, name='team'),
    path('company/scenario/', platform.scenario, name='scenario'),
    path('mentor/', platform.mentor, name='mentor'),
    path('conversation/<int:pk>/delete/', platform.delete_conversation, name='delete_conversation'),
    path('manager/', platform.mentor, {'role': 'manager'}, name='manager'),
    path('notifications/', platform.notifications, name='notifications'),
    path('notifications/<int:pk>/read/', platform.notification_read, name='notification_read'),
    path('results/', platform.results, name='results'),
    path('report/', platform.report, name='report'),
    path('reviewer/', platform.reviewer, name='reviewer'),
    path('content/', platform.content_admin, name='content_admin'),
    path('states/', platform.states, name='states'),
    path('password/reset/', auth_views.PasswordResetView.as_view(template_name='projects/password_form.html', email_template_name='projects/password_email.txt'), name='password_reset'),
    path('password/change/', auth_views.PasswordChangeView.as_view(template_name='projects/password_change.html'), name='password_change'),
    path('password/changed/', auth_views.PasswordChangeDoneView.as_view(template_name='projects/password_changed.html'), name='password_change_done'),
    path('password/sent/', auth_views.PasswordResetDoneView.as_view(template_name='projects/password_sent.html'), name='password_reset_done'),
    path('password/new/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='projects/password_form.html'), name='password_reset_confirm'),
    path('password/done/', auth_views.PasswordResetCompleteView.as_view(template_name='projects/password_done.html'), name='password_reset_complete'),
]
