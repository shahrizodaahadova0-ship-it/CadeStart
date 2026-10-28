import json
import time
from smtplib import SMTPException

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.db import transaction
from django.db.models import Q, OuterRef, Subquery
from django.core.cache import cache
from django.core import signing
from django.core.paginator import Paginator
from django.utils.http import url_has_allowed_host_and_scheme
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .catalog import LESSONS, QUESTIONS
from .forms import ProfileForm, ProposalForm, ReviewForm, SubmissionForm, SubmissionDraftForm, AIQuestionForm, CommentForm, LessonCheckForm
from .lesson_checks import questions_for
from .curriculum import get_lessons, get_tasks
from .models import ChangeProposal, LessonProgress, Notification, Profile, Submission, SubmissionDraft, AIConversation, AIMessage, SubmissionComment
from . import ai_service


def item(items, slug):
    return next((entry for entry in items if entry['slug'] == slug), None)


def page(request, template, **context):
    language = request.session.get('language', 'ru')
    if request.user.is_authenticated:
        try:
            language = request.user.profile.language
        except Profile.DoesNotExist:
            pass
    if language == 'uz':
        def localize(value):
            if isinstance(value, dict):
                result = {key: localize(entry) for key, entry in value.items()}
                for key, entry in value.items():
                    if key.startswith('uz_'):
                        result[key[3:]] = localize(entry)
                return result
            if isinstance(value, list):
                return [localize(entry) for entry in value]
            return value
        context = localize(context)
    return render(request, f'projects/{template}.html', context)


def learning_data(user):
    progress = {p.lesson: p for p in LessonProgress.objects.filter(user=user)}
    lessons = [{**lesson, 'done': bool(progress.get(lesson['slug']) and progress[lesson['slug']].completed),
                'quiz_score': progress[lesson['slug']].quiz_score if lesson['slug'] in progress else None} for lesson in get_lessons()]
    completed = sum(lesson['done'] for lesson in lessons)
    try:
        recommended = user.profile.recommended_lesson
    except Profile.DoesNotExist:
        recommended = 'basics'
    remaining = [lesson for lesson in lessons if not lesson['done']]
    current = next((lesson for lesson in remaining if lesson['slug'] == recommended),
                   remaining[0] if remaining else lessons[-1])
    return {'lessons': lessons, 'completed': completed, 'total': len(lessons),
            'percent': round(completed / len(lessons) * 100), 'current': current,
            'all_completed': not remaining, 'checked_lessons': sum(lesson['quiz_score'] is not None for lesson in lessons)}


def latest_submissions(user):
    latest = Submission.objects.filter(user=user, task=OuterRef('task')).order_by('-created_at', '-pk')
    return Submission.objects.filter(user=user, pk=Subquery(latest.values('pk')[:1])).order_by('-created_at', '-pk')


@login_required
def dashboard(request):
    data = learning_data(request.user)
    return page(request, 'dashboard', active='dashboard', **data,
                accepted=latest_submissions(request.user).filter(status='done').count(),
                pending=latest_submissions(request.user).filter(status='review').count(), task=item(get_tasks(), 'cart'))


@login_required
def learning(request):
    return page(request, 'learning', active='learning', **learning_data(request.user))


@login_required
def lesson(request, slug):
    curriculum = get_lessons()
    lesson_data = item(curriculum, slug)
    if not lesson_data:
        raise Http404
    progress = LessonProgress.objects.filter(user=request.user, lesson=slug).first()
    action = request.POST.get('action', 'save')
    if request.method == 'POST' and action not in ('save', 'complete', 'check', 'reopen'):
        return HttpResponse(status=400)
    if request.method == 'POST' and action == 'reopen':
        if progress and progress.completed:
            progress.completed = False
            progress.save(update_fields=['completed', 'updated_at'])
            messages.success(request, 'Урок возвращён к повторению. Заметки и самопроверка сохранены. / Dars takrorlashga qaytarildi. Qaydlar va tekshiruv saqlandi.')
        return redirect('lesson', slug=slug)
    questions = questions_for(slug)
    checking = request.method == 'POST' and request.POST.get('action') == 'check'
    language = request.user.profile.language
    quiz_form = LessonCheckForm(questions, language, request.POST if checking else None,
                               initial=progress.quiz_answers if progress else {})
    if checking and not questions:
        return HttpResponse(status=400)
    if checking and quiz_form.is_valid():
        if progress is None:
            progress = LessonProgress(user=request.user, lesson=slug, code=lesson_data['code'])
        correct = sum(quiz_form.cleaned_data[f'answer_{index}'] == question['correct'] for index, question in enumerate(questions))
        progress.quiz_score = round(correct / len(questions) * 100)
        progress.quiz_answers = quiz_form.cleaned_data
        progress.save()
        return redirect(reverse('lesson', args=[slug]) + '#self-check')
    code_error = request.method == 'POST' and not checking and len(request.POST.get('code', '')) > 20000
    if code_error:
        messages.error(request, 'Заметки не сохранены: максимум 20 000 символов. Сократите текст и сохраните снова. / Qaydlar saqlanmadi: ko‘pi bilan 20 000 belgi. Matnni qisqartiring va qayta saqlang.')
    if request.method == 'POST' and not checking and not code_error:
        if progress is None:
            progress = LessonProgress(user=request.user, lesson=slug)
        if 'code' in request.POST:
            progress.code = request.POST['code']
        if request.POST.get('action') == 'complete':
            progress.completed = True
            messages.success(request, 'Урок отмечен как изученный. / Dars o‘rganildi.')
        progress.save()
        if request.POST.get('action') == 'complete':
            return redirect('learning')
        messages.success(request, 'Черновик сохранён. / Qoralama saqlandi.')
        return redirect('lesson', slug=slug)
    return page(request, 'lesson', active='learning', lesson=lesson_data,
                previous_lesson=curriculum[curriculum.index(lesson_data) - 1] if curriculum.index(lesson_data) > 0 else None,
                next_lesson=curriculum[curriculum.index(lesson_data) + 1] if curriculum.index(lesson_data) + 1 < len(curriculum) else None,
                quiz_form=quiz_form,
                quiz_fields=[{'field': quiz_form[f'answer_{index}'], 'code': question.get('uz_code', question['code']) if language == 'uz' else question['code'],
                              'explanation': question['uz_explanation'] if language == 'uz' else question['explanation'],
                              'correct': progress.quiz_answers.get(f'answer_{index}') == question['correct'] if progress else False}
                             for index, question in enumerate(questions)],
                code=request.POST['code'] if code_error else (progress.code if progress is not None else lesson_data['code']), progress=progress)


@login_required
def onboarding(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        experience = request.POST.get('experience')
        hours = request.POST.get('hours')
        if experience in ('beginner', 'basics', 'projects', 'experienced') and hours in ('3-5', '5-10', '10+'):
            profile.experience, profile.weekly_hours, profile.onboarded = experience, hours, True
            if experience == 'beginner':
                profile.recommended_lesson = 'basics'
            profile.save()
            return redirect('diagnostic' if experience != 'beginner' else 'dashboard')
        messages.error(request, 'Выберите уровень и время. / Daraja va vaqtni tanlang.')
    return page(request, 'onboarding', profile=profile)


@login_required
def diagnostic(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        answers = {}
        for index, question in enumerate(QUESTIONS):
            value = request.POST.get(f'q{index}', 'skip')
            answers[f'q{index}'] = value if value in [str(i) for i in range(len(question['answers']))] else 'skip'
        if request.POST.get('action') == 'save':
            try:
                step = max(0, min(int(request.POST.get('step', '0')), len(QUESTIONS) - 1))
            except (ValueError, TypeError):
                step = 0
            profile.diagnostic_draft = {'answers': answers, 'step': step}
            profile.save(update_fields=['diagnostic_draft'])
            messages.success(request, 'Прогресс теста сохранён. / Test jarayoni saqlandi.')
            return redirect('dashboard')
        score = sum(answers[f'q{index}'] == q['correct'] for index, q in enumerate(QUESTIONS))
        weak_topics = {q['lesson'] for index, q in enumerate(QUESTIONS) if answers[f'q{index}'] != q['correct']}
        profile.recommended_lesson = next((lesson['slug'] for lesson in LESSONS if lesson['slug'] in weak_topics), 'testing')
        profile.diagnostic_score = round(score / len(QUESTIONS) * 100)
        profile.diagnostic_answers = answers
        profile.diagnostic_draft = {}
        profile.save(update_fields=['diagnostic_score', 'diagnostic_answers', 'diagnostic_draft', 'recommended_lesson'])
        return redirect('diagnostic_result')
    draft = profile.diagnostic_draft
    questions = [{**q, 'selected': draft.get('answers', {}).get(f'q{index}', 'skip')} for index, q in enumerate(QUESTIONS)]
    return page(request, 'diagnostic', active='learning', questions=questions, step=draft.get('step', 0))


@login_required
def diagnostic_result(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    curriculum = get_lessons()
    topic_results = []
    for lesson in curriculum:
        indexes = [i for i, q in enumerate(QUESTIONS) if q['lesson'] == lesson['slug']]
        if indexes and profile.diagnostic_answers:
            correct = sum(profile.diagnostic_answers.get(f'q{i}') == QUESTIONS[i]['correct'] for i in indexes)
            topic_results.append({**lesson, 'correct': correct, 'count': len(indexes)})
    return page(request, 'diagnostic_result', active='learning', profile=profile,
                recommendation=item(curriculum, profile.recommended_lesson) or curriculum[0], topic_results=topic_results)


@login_required
def company(request):
    return page(request, 'company', active='company', tasks=get_tasks(),
                submissions=Submission.objects.filter(user=request.user).order_by('-created_at')[:5])


@login_required
def kanban(request):
    submissions = Submission.objects.filter(user=request.user).order_by('created_at', 'pk')
    latest = {s.task: s for s in submissions}
    drafts = {draft.task: draft for draft in SubmissionDraft.objects.filter(user=request.user)}
    query = request.GET.get('q', '').strip()[:200]
    status = request.GET.get('status', '')
    if status not in ('todo', 'inprogress', 'review', 'changes', 'done'):
        status = ''
    matching = [task for task in get_tasks() if not query or any(
        query.casefold() in str(task.get(field, '')).casefold()
        for field in ('id', 'title', 'uz', 'description', 'uz_description', 'tag')
    )]
    columns = []
    for key, title, uz in [('todo', 'Задачи', 'Vazifalar'), ('inprogress', 'В работе', 'Jarayonda'), ('review', 'На проверке', 'Tekshiruvda'), ('changes', 'Доработка', 'Tuzatish kerak'), ('done', 'Готово', 'Bajarildi')]:
        if status and status != key:
            continue
        tasks = [{**task, 'submission': latest.get(task['slug']), 'draft': drafts.get(task['slug'])} for task in matching
                 if (latest[task['slug']].status if task['slug'] in latest else 'inprogress' if task['slug'] in drafts else 'todo') == key]
        columns.append({'key': key, 'title': title, 'uz': uz, 'tasks': tasks})
    return page(request, 'kanban', active='company', columns=columns, query=query,
                selected_status=status, found=sum(len(column['tasks']) for column in columns))


@login_required
def task_detail(request, slug):
    task = item(get_tasks(), slug)
    if not task:
        raise Http404
    return page(request, 'task', active='company', task=task,
                draft=SubmissionDraft.objects.filter(user=request.user, task=slug).exists(),
                latest=Submission.objects.filter(user=request.user, task=slug).order_by('-created_at', '-pk').first())


@login_required
@transaction.atomic
def submit(request, slug):
    task = item(get_tasks(), slug)
    if not task:
        raise Http404
    if request.method == 'POST' and request.POST.get('action', 'submit') not in ('submit', 'draft', 'discard'):
        return HttpResponse(status=400)
    draft = SubmissionDraft.objects.filter(user=request.user, task=slug).first()
    if request.method == 'POST' and request.POST.get('action') == 'discard':
        if draft:
            draft.delete()
        messages.success(request, 'Черновик удалён. / Qoralama o‘chirildi.')
        return redirect('submit', slug=slug)
    saving_draft = request.method == 'POST' and request.POST.get('action') == 'draft'
    form_class = SubmissionDraftForm if saving_draft else SubmissionForm
    initial = {field: getattr(draft, field) for field in ('repository', 'commit', 'description')} if draft else {}
    form = form_class(request.POST if request.method == 'POST' else None, initial=initial)
    if request.method == 'POST' and not saving_draft and request.POST.get('task_revision') != str(task['revision']):
        form.add_error(None, 'Требования задания изменились или версия не указана. Проверьте текущие критерии перед повторной отправкой. / Vazifa talablari o‘zgargan yoki versiya ko‘rsatilmagan. Qayta yuborishdan oldin mezonlarni tekshiring.')
    if request.method == 'POST' and form.is_valid():
        if saving_draft:
            SubmissionDraft.objects.update_or_create(user=request.user, task=slug, defaults={
                field: form.cleaned_data[field] for field in ('repository', 'commit', 'description')
            })
            messages.success(request, 'Черновик сохранён в аккаунте. / Qoralama hisobda saqlandi.')
            return redirect('submit', slug=slug)
        submission = form.save(commit=False)
        submission.user, submission.task = request.user, slug
        submission.task_snapshot = {key: value for key, value in task.items() if key != 'content_id'}
        submission.save()
        if draft:
            draft.delete()
        Notification.objects.create(user=request.user, title='Решение отправлено / Yechim yuborildi',
                                    text=task['title'], url=reverse('review_result', args=[submission.pk]))
        messages.success(request, 'Решение сохранено и ожидает назначения ревьюера. / Yechim saqlandi.')
        return redirect('review_result', pk=submission.pk)
    return page(request, 'submit', active='company', task=task, form=form,
                draft=draft,
                history=Submission.objects.filter(user=request.user, task=slug).order_by('-created_at'))


@login_required
def review_result(request, pk):
    submission = get_object_or_404(Submission, pk=pk, user=request.user)
    return page(request, 'review_result', active='company', submission=submission, task=submission.task_snapshot or item(get_tasks(), submission.task))


@login_required
def discussion(request, pk):
    access = Q(user=request.user)
    if request.user.is_staff:
        access |= Q(reviewer=request.user)
    submission = get_object_or_404(Submission.objects.filter(access).select_related('user', 'reviewer'), pk=pk)
    form = CommentForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            SubmissionComment.objects.create(submission=submission, author=request.user, body=form.cleaned_data['body'])
            recipient = submission.reviewer if request.user.pk == submission.user_id else submission.user
            if recipient and recipient.pk != request.user.pk:
                Notification.objects.create(user=recipient, title='Новый комментарий к решению / Yechimga yangi izoh',
                                            text=f'{submission.task} · {request.user.username}',
                                            url=reverse('discussion', args=[submission.pk]))
        return redirect('discussion', pk=submission.pk)
    comments = Paginator(submission.comments.select_related('author').order_by('created_at', 'pk'), 25)
    return page(request, 'discussion', active='company', submission=submission,
                task=submission.task_snapshot or item(get_tasks(), submission.task), form=form,
                comments=comments.get_page(request.GET.get('page', comments.num_pages)),
                is_owner=submission.user_id == request.user.pk)


@login_required
def mentor(request, role='mentor'):
    if not ai_service.available():
        if request.method == 'POST':
            messages.error(request, 'AI не подключён. Вопрос не отправлен. / AI ulanmagan. Savol yuborilmadi.')
        return page(request, 'mentor', active=role, role=role, lessons=get_lessons()[:5])
    conversations = AIConversation.objects.filter(user=request.user, role=role).order_by('-pk')
    thread_id = request.POST.get('conversation') if request.method == 'POST' else request.GET.get('conversation')
    conversation = None
    if thread_id:
        try:
            thread_id = int(thread_id)
            if not 0 < thread_id < 2 ** 63:
                raise ValueError
        except (ValueError, TypeError):
            raise Http404
        conversation = get_object_or_404(conversations, pk=thread_id)
    form = AIQuestionForm(request.POST if request.method == 'POST' else None)
    chat_messages = conversation.messages.order_by('pk') if conversation else AIMessage.objects.none()
    if request.method == 'POST' and form.is_valid():
        limit_key = f'ai-send:{request.user.pk}'
        if not cache.add(limit_key, True, timeout=10):
            form.add_error(None, 'Подождите несколько секунд перед следующим сообщением. / Keyingi xabargacha bir necha soniya kuting.')
        else:
            try:
                recent = list(chat_messages.order_by('-pk').values('role', 'content')[:10])[::-1]
                response = ai_service.answer(form.cleaned_data['question'], recent, role, request.user.profile.language)
            except ai_service.AIUnavailable:
                form.add_error(None, 'Не удалось получить ответ AI. Ваш вопрос остался в форме; попробуйте позже. / AI javobini olish imkoni bo‘lmadi. Savol shaklda qoldi; keyinroq urinib ko‘ring.')
            else:
                with transaction.atomic():
                    if conversation is None:
                        conversation = AIConversation.objects.create(user=request.user, role=role, title=form.cleaned_data['question'][:100])
                    AIMessage.objects.create(conversation=conversation, role='user', content=form.cleaned_data['question'])
                    AIMessage.objects.create(conversation=conversation, role='assistant', content=response)
                return redirect(reverse(role) + f'?conversation={conversation.pk}')
    return page(request, 'ai_chat', active=role, role=role, form=form, conversation=conversation,
                conversations=conversations[:20], chat_messages=chat_messages)


@login_required
@require_POST
def delete_conversation(request, pk):
    conversation = get_object_or_404(AIConversation, pk=pk, user=request.user)
    role = conversation.role
    conversation.delete()
    return redirect(role)


@login_required
def documents(request):
    return page(request, 'documents', active='company')


@login_required
def team(request):
    return page(request, 'team', active='company')


@login_required
def scenario(request):
    form = ProposalForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        proposal = form.save(commit=False)
        proposal.user = request.user
        proposal.save()
        messages.success(request, 'Предложение сохранено. / Taklif saqlandi.')
        return redirect('scenario')
    return page(request, 'scenario', active='company', form=form,
                proposals=ChangeProposal.objects.filter(user=request.user).order_by('-created_at'))


@login_required
def notifications(request):
    if request.method == 'POST':
        Notification.objects.filter(user=request.user).update(read=True)
        return redirect('notifications')
    entries = Notification.objects.filter(user=request.user).order_by('-created_at')
    if request.GET.get('filter') == 'unread':
        entries = entries.filter(read=False)
    entries = Paginator(entries.order_by('-created_at', '-pk'), 15).get_page(request.GET.get('page'))
    return page(request, 'notifications', active='notifications', notifications=entries)


@login_required
@require_POST
def notification_read(request, pk):
    entry = get_object_or_404(Notification, pk=pk, user=request.user)
    if not entry.read:
        entry.read = True
        entry.save(update_fields=['read'])
    if request.POST.get('action') == 'open' and url_has_allowed_host_and_scheme(
        entry.url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(entry.url)
    url = reverse('notifications')
    if request.POST.get('filter') == 'unread':
        url += '?filter=unread'
    return redirect(url)


@login_required
def results(request):
    latest = latest_submissions(request.user)
    history = request.GET.get('view') == 'history'
    submissions = Submission.objects.filter(user=request.user).order_by('-created_at', '-pk') if history else latest
    status = request.GET.get('status', '')
    if status in dict(Submission.STATUS_CHOICES):
        submissions = submissions.filter(status=status)
    else:
        status = ''
    return page(request, 'results', active='results', **learning_data(request.user),
                submissions=Paginator(submissions, 10).get_page(request.GET.get('page')),
                submission_count=Submission.objects.filter(user=request.user).count(),
                accepted=latest.filter(status='done').count(), history=history, selected_status=status)


@login_required
def report(request):
    data = learning_data(request.user)
    submissions = Submission.objects.filter(user=request.user).order_by('-created_at', '-pk')
    latest = latest_submissions(request.user)
    if request.GET.get('format') in ('json', 'markdown'):
        def entry_data(entry):
            return {'id': entry.pk, 'task': entry.task, 'title': entry.task_title,
                    'task_revision': entry.task_snapshot.get('revision'),
                    'task_requirements': entry.task_snapshot.get('requirements', []),
                    'status': entry.status, 'score': entry.score, 'feedback': entry.feedback,
                    'repository': entry.repository, 'description': entry.description,
                    'commit': entry.commit, 'created_at': entry.created_at.isoformat()}
        payload = {'student': request.user.get_full_name() or request.user.username,
                   'completed_lessons': data['completed'], 'total_lessons': data['total'],
                   'accepted_tasks': latest.filter(status='done').count(),
                   'lesson_checks': [{'lesson': lesson['slug'], 'title': lesson['title'], 'score': lesson['quiz_score']}
                                     for lesson in data['lessons'] if lesson['quiz_score'] is not None],
                   'latest_submissions': [entry_data(entry) for entry in latest],
                   'submissions': [entry_data(entry) for entry in submissions]}
        if request.GET['format'] == 'json':
            content, kind, filename = json.dumps(payload, ensure_ascii=False, indent=2), 'application/json', 'codestart-report.json'
        else:
            lines = ['# CodeStart — учебный отчёт', f"Уроки: {data['completed']} / {data['total']}",
                     f"Принято задач по последним версиям: {payload['accepted_tasks']}", '', '## Последние версии по задачам', '']
            lines += [f"- {s['title']} (#{s['id']}): {s['status']}" for s in payload['latest_submissions']]
            lines += ['', '## История всех отправок', '']
            for entry in payload['submissions']:
                lines += [f"### {entry['title']} (#{entry['id']})", '',
                          f"Дата: {entry['created_at']}", f"Статус: {entry['status']}",
                          f"Версия задания: {entry['task_revision'] or '—'}",
                          f"Оценка: {entry['score'] if entry['score'] is not None else '—'} / 100",
                          f"Репозиторий: {entry['repository']}", f"Commit: {entry['commit'] or '—'}", '',
                          'Описание решения:', entry['description'], '', 'Критерии задания:']
                lines += [f"- {requirement}" for requirement in entry['task_requirements']]
                lines += ['', 'Комментарий ревьюера:', entry['feedback'] or '—', '']
            lines += ['', '## Самопроверки уроков', '']
            lines += [f"- {check['title']}: {check['score']} / 100" for check in payload['lesson_checks']]
            content, kind, filename = '\n'.join(lines), 'text/markdown; charset=utf-8', 'codestart-report.md'
        response = HttpResponse(content, content_type=kind)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    return page(request, 'report', active='results', submissions=latest,
                submission_count=submissions.count(), accepted=latest.filter(status='done').count(), **data)


@login_required
def settings_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    form = ProfileForm(request.POST or None, instance=profile, initial={
        'first_name': request.user.first_name, 'email': request.user.email,
    })
    if request.method == 'POST' and form.is_valid():
        form.save()
        request.user.first_name = form.cleaned_data['first_name']
        if request.user.email != form.cleaned_data['email']:
            profile.email_verified = False
            profile.save(update_fields=['email_verified'])
        request.user.email = form.cleaned_data['email']
        request.user.save(update_fields=['first_name', 'email'])
        messages.success(request, 'Настройки сохранены. / Sozlamalar saqlandi.')
        return redirect('profile')
    return page(request, 'settings', active='profile', form=form, profile=profile)


@staff_member_required(login_url='login')
@transaction.atomic
def reviewer(request):
    base = Submission.objects.filter(reviewer=request.user).select_related('user').order_by('-created_at', '-pk')
    counts = {key: base.filter(status=key).count() for key in ('review', 'changes', 'done')}
    query = request.GET.get('q', '').strip()[:200]
    status = request.GET.get('status', '')
    if status not in counts:
        status = ''
    assigned = base
    if query:
        assigned = assigned.filter(Q(user__username__icontains=query) | Q(user__first_name__icontains=query) | Q(task__icontains=query))
    if status:
        assigned = assigned.filter(status=status)
    selected_id = request.POST.get('submission') or request.GET.get('submission')
    if selected_id:
        try:
            selected_id = int(selected_id)
            if not 0 < selected_id < 2 ** 63:
                raise ValueError
        except (ValueError, TypeError):
            raise Http404
        selected = get_object_or_404(base, pk=selected_id)
    elif request.method == 'POST':
        return HttpResponse(status=400)
    else:
        selected = assigned.first()
    form = ReviewForm(request.POST or None, instance=selected) if selected else None
    if request.method == 'POST' and selected and form.is_valid():
        if not form.has_changed():
            messages.info(request, 'Изменений нет. / O‘zgarishlar yo‘q.')
            return redirect(request.get_full_path())
        reviewed = form.save()
        Notification.objects.create(user=reviewed.user, title='Проверка обновлена / Tekshiruv yangilandi',
                                    text=reviewed.get_status_display(), url=reverse('review_result', args=[reviewed.pk]))
        messages.success(request, 'Результат проверки сохранён. / Natija saqlandi.')
        return redirect(request.get_full_path())
    return page(request, 'reviewer', active='reviewer', assigned=assigned, selected=selected,
                form=form, query=query, selected_status=status, counts=counts)


@staff_member_required(login_url='login')
def content_admin(request):
    can_manage_submissions = request.user.has_perm('projects.change_submission')
    can_manage_proposals = request.user.has_perm('projects.change_changeproposal')
    return page(request, 'content_admin', active='content_admin', lessons=get_lessons(), tasks=get_tasks(),
                can_manage_submissions=can_manage_submissions, can_manage_proposals=can_manage_proposals,
                unassigned_count=Submission.objects.filter(status='review', reviewer__isnull=True).count() if can_manage_submissions else None,
                pending_review_count=Submission.objects.filter(status='review').count() if can_manage_submissions else None,
                pending_proposal_count=ChangeProposal.objects.filter(status='pending').count() if can_manage_proposals else None)


@login_required
def states(request):
    return page(request, 'states', active='states')


@login_required
def email_verification(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST' and request.user.email and not profile.email_verified:
        last = request.session.get('verification_sent', 0)
        if time.time() - last < 60:
            messages.info(request, 'Повторная отправка доступна через минуту. / Bir daqiqadan so‘ng qayta yuborish mumkin.')
        else:
            token = signing.dumps({'user': request.user.pk, 'email': request.user.email}, salt='codestart-email')
            url = request.build_absolute_uri(reverse('verify_email', args=[token]))
            try:
                send_mail('CodeStart — подтвердите email / emailni tasdiqlang',
                          f'Подтвердите email / Emailni tasdiqlang:\n{url}\n\nСсылка действует 24 часа / Havola 24 soat amal qiladi.',
                          settings.DEFAULT_FROM_EMAIL, [request.user.email])
            except (OSError, SMTPException):
                messages.error(request, 'Не удалось отправить письмо. Попробуйте позже. / Xat yuborib bo‘lmadi. Keyinroq urinib ko‘ring.')
                return redirect('email_verification')
            request.session['verification_sent'] = time.time()
            messages.success(request, 'Письмо передано почтовому сервису. / Xat pochta xizmatiga topshirildi.')
        return redirect('email_verification')
    return page(request, 'email_verification', profile=profile)


@login_required
def verify_email(request, token):
    try:
        data = signing.loads(token, salt='codestart-email', max_age=86400)
    except signing.BadSignature:
        messages.error(request, 'Ссылка недействительна или устарела. / Havola noto‘g‘ri yoki eskirgan.')
        return redirect('email_verification')
    if data['user'] == request.user.pk and data['email'] == request.user.email:
        profile, _ = Profile.objects.get_or_create(user=request.user)
        profile.email_verified = True
        profile.save(update_fields=['email_verified'])
        messages.success(request, 'Email подтверждён. / Email tasdiqlandi.')
    else:
        messages.error(request, 'Ссылка относится к другому аккаунту. / Havola boshqa hisobga tegishli.')
    return redirect('email_verification')


@require_POST
def logout_post(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('home')
