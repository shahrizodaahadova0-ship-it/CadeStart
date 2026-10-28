from django.contrib import admin
from django.urls import reverse
from django.utils import timezone
from django.db import transaction
from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.html import format_html, format_html_join
import json
from .models import Project, Profile, LessonProgress, Submission, Notification, ChangeProposal, LessonContent, TaskContent, ContentEdit
from .forms import SubmissionAdminForm, TaskContentForm


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'level', 'created_at')
    list_filter = ('category', 'level')
    search_fields = ('title', 'description')


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    form = SubmissionAdminForm
    list_display = ('task', 'user', 'status', 'reviewer', 'score', 'created_at')
    list_filter = ('status', 'reviewer')
    search_fields = ('user__username', 'task')
    readonly_fields = ('user', 'task', 'task_snapshot', 'repository', 'commit', 'description', 'created_at')

    def has_add_permission(self, request):
        return False

    def save_model(self, request, obj, form, change):
        previous = Submission.objects.get(pk=obj.pk)
        assignment_changed = previous.reviewer_id != obj.reviewer_id
        review_changed = (previous.status, previous.feedback, previous.score) != (obj.status, obj.feedback, obj.score)
        super().save_model(request, obj, form, change)
        if assignment_changed and obj.reviewer_id:
            Notification.objects.create(user=obj.reviewer, title='Назначена проверка / Tekshiruv tayinlandi',
                                        text=f'{obj.task} · {obj.user.username}', url=reverse('reviewer') + f'?submission={obj.pk}')
        if review_changed:
            Notification.objects.create(user=obj.user, title='Проверка обновлена / Tekshiruv yangilandi',
                                        text=f'{obj.get_status_display()} / {obj.status_uz}',
                                        url=reverse('review_result', args=[obj.pk]))


@admin.register(ChangeProposal)
class ChangeProposalAdmin(admin.ModelAdmin):
    list_display = ('user', 'hours', 'days', 'status', 'reviewed_by', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'question')
    readonly_fields = ('user', 'question', 'hours', 'days', 'created_at', 'reviewed_by', 'reviewed_at')

    def has_add_permission(self, request):
        return False

    def save_model(self, request, obj, form, change):
        previous = ChangeProposal.objects.get(pk=obj.pk)
        decision_changed = (previous.status, previous.feedback) != (obj.status, obj.feedback)
        if decision_changed:
            obj.reviewed_by = request.user if obj.status != 'pending' else None
            obj.reviewed_at = timezone.now() if obj.status != 'pending' else None
        super().save_model(request, obj, form, change)
        if decision_changed:
            Notification.objects.create(user=obj.user, title='Решение по предложению / Taklif bo‘yicha qaror',
                                        text=f'{obj.get_status_display()} / {obj.status_uz}', url=reverse('scenario'))


admin.site.register([Profile, LessonProgress, Notification])


class ContentAuditMixin:
    @transaction.atomic
    def save_model(self, request, obj, form, change):
        previous = type(obj).objects.get(pk=obj.pk)
        before = {field: getattr(previous, field) for field in self.audit_fields}
        super().save_model(request, obj, form, change)
        after = {field: getattr(obj, field) for field in self.audit_fields}
        changed = [field for field in self.audit_fields if before[field] != after[field]]
        if changed:
            if hasattr(obj, 'revision'):
                before['revision'], after['revision'] = previous.revision, obj.revision
            ContentEdit.objects.create(kind=self.audit_kind, slug=obj.slug, author=request.user,
                                       before=before, after=after, changed_fields=changed)


@admin.register(LessonContent)
class LessonContentAdmin(ContentAuditMixin, admin.ModelAdmin):
    audit_kind = 'lesson'
    audit_fields = ('title', 'title_uz', 'summary', 'summary_uz', 'text', 'text_uz', 'hint', 'hint_uz', 'code', 'minutes')
    list_display = ('title', 'slug', 'minutes', 'updated_at')
    search_fields = ('title', 'title_uz', 'text', 'text_uz')
    readonly_fields = ('slug', 'updated_at')
    fieldsets = (
        (None, {'fields': ('slug', 'minutes', 'updated_at')}),
        ('Русский', {'fields': ('title', 'summary', 'text', 'hint')}),
        ('O‘zbekcha', {'fields': ('title_uz', 'summary_uz', 'text_uz', 'hint_uz')}),
        ('Code', {'fields': ('code',)}),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TaskContent)
class TaskContentAdmin(ContentAuditMixin, admin.ModelAdmin):
    audit_kind = 'task'
    audit_fields = ('title', 'title_uz', 'description', 'description_uz', 'requirements', 'requirements_uz', 'tag', 'priority')
    form = TaskContentForm
    list_display = ('title', 'slug', 'priority', 'revision', 'updated_at')
    list_filter = ('priority', 'tag')
    search_fields = ('title', 'title_uz', 'description', 'description_uz')
    readonly_fields = ('slug', 'revision', 'updated_at')
    fieldsets = (
        (None, {'fields': ('slug', 'revision', 'updated_at', 'tag', 'priority')}),
        ('Русский', {'fields': ('title', 'description', 'requirements')}),
        ('O‘zbekcha', {'fields': ('title_uz', 'description_uz', 'requirements_uz')}),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ContentEdit)
class ContentEditAdmin(admin.ModelAdmin):
    change_form_template = 'projects/admin/contentedit_change_form.html'
    list_display = ('slug', 'kind', 'author', 'created_at')
    list_filter = ('kind',)
    search_fields = ('slug', 'author__username')
    readonly_fields = ('kind', 'slug', 'author', 'created_at', 'formatted_changes', 'before', 'after')

    @admin.display(description='Изменённые поля / O‘zgargan maydonlar')
    def formatted_changes(self, obj):
        def display(value):
            return json.dumps(value, ensure_ascii=False, indent=2) if isinstance(value, (list, dict)) else str(value)
        rows = format_html_join('', '<tr><th>{}</th><td><pre style="white-space:pre-wrap;max-width:34vw;overflow-wrap:anywhere">{}</pre></td><td><pre style="white-space:pre-wrap;max-width:34vw;overflow-wrap:anywhere">{}</pre></td></tr>',
                                ((field, display(obj.before.get(field, '')), display(obj.after.get(field, ''))) for field in obj.changed_fields))
        return format_html('<table><thead><tr><th>Поле / Maydon</th><th>До / Oldin</th><th>После / Keyin</th></tr></thead><tbody>{}</tbody></table>', rows)

    def can_restore(self, request, obj):
        model = 'lessoncontent' if obj.kind == 'lesson' else 'taskcontent'
        return request.user.has_perm(f'projects.change_{model}')

    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)
        context = dict(extra_context or {})
        context['can_restore_content'] = bool(obj and self.can_restore(request, obj))
        return super().change_view(request, object_id, form_url, context)

    def get_urls(self):
        return [path('<int:object_id>/restore/', self.admin_site.admin_view(self.restore_view), name='projects_contentedit_restore')] + super().get_urls()

    @transaction.atomic
    def restore_view(self, request, object_id):
        entry = self.get_object(request, object_id)
        if not entry:
            raise Http404
        if not self.can_restore(request, entry):
            raise PermissionDenied
        model = LessonContent if entry.kind == 'lesson' else TaskContent
        obj = model.objects.select_for_update().filter(slug=entry.slug).first()
        if obj is None:
            raise Http404
        state = {'entry': entry.pk, 'kind': entry.kind, 'slug': entry.slug, 'updated': obj.updated_at.isoformat()}
        errors = []
        target_admin = self.admin_site._registry[model]
        if request.method == 'POST':
            try:
                confirmed = signing.loads(request.POST.get('token', ''), salt='restore-content', max_age=900)
            except signing.BadSignature:
                confirmed = None
            if confirmed != state:
                errors.append('Материал изменился или подтверждение устарело. Проверьте версии заново. / Material o‘zgargan yoki tasdiq eskirgan. Versiyalarni qayta tekshiring.')
            elif not all(field in entry.before for field in target_admin.audit_fields):
                errors.append('В этой записи недостаточно данных для восстановления. / Ushbu yozuvda tiklash uchun ma’lumot yetarli emas.')
            else:
                for field in target_admin.audit_fields:
                    setattr(obj, field, entry.before[field])
                try:
                    obj.full_clean()
                except ValidationError:
                    obj.refresh_from_db()
                    errors.append('Прежняя редакция не соответствует текущим правилам заполнения. / Oldingi tahrir joriy qoidalarga mos kelmaydi.')
                else:
                    target_admin.save_model(request, obj, None, True)
                    target_admin.log_change(request, obj, f'Restored content before history entry #{entry.pk}.')
                    self.message_user(request, 'Прежняя редакция восстановлена. / Oldingi tahrir tiklandi.')
                    return redirect(f'admin:projects_{model._meta.model_name}_change', obj.pk)
        context = {**self.admin_site.each_context(request), 'title': 'Восстановление редакции / Tahrirni tiklash',
                   'entry': entry, 'material': obj, 'restore_token': signing.dumps(state, salt='restore-content'),
                   'restore_errors': errors, 'opts': self.model._meta,
                   'target_text': json.dumps(entry.before, ensure_ascii=False, indent=2),
                   'current_text': json.dumps({field: getattr(obj, field) for field in target_admin.audit_fields}, ensure_ascii=False, indent=2)}
        return TemplateResponse(request, 'projects/admin/content_restore.html', context)

    def allowed_kinds(self, request):
        return [kind for kind, model in [('lesson', 'lessoncontent'), ('task', 'taskcontent')]
                if request.user.has_perm(f'projects.view_{model}') or request.user.has_perm(f'projects.change_{model}')]

    def get_queryset(self, request):
        return super().get_queryset(request).filter(kind__in=self.allowed_kinds(request)).select_related('author')

    def has_view_permission(self, request, obj=None):
        kinds = self.allowed_kinds(request)
        return obj.kind in kinds if obj else bool(kinds)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
