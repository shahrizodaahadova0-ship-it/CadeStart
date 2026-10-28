from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Project(models.Model):
    CATEGORY_CHOICES = [
        ('python', 'Python'),
        ('django', 'Django'),
        ('web', 'HTML / CSS / JS'),
        ('bot', 'Telegram Bots'),
        ('database', 'Database'),
    ]

    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES
    )
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES
    )
    technologies = models.CharField(max_length=300)
    code = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Profile(models.Model):
    LANGUAGE_CHOICES = [
        ('ru', 'Русский'),
        ('uz', "O'zbekcha"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    language = models.CharField(
        max_length=2,
        choices=LANGUAGE_CHOICES,
        default='ru'
    )
    experience = models.CharField(max_length=20, default='beginner')
    weekly_hours = models.CharField(max_length=10, default='5-10')
    timezone = models.CharField(max_length=50, default='Asia/Tashkent')
    github = models.URLField(blank=True)
    paused = models.BooleanField(default=False)
    onboarded = models.BooleanField(default=False)
    diagnostic_score = models.PositiveSmallIntegerField(null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    recommended_lesson = models.SlugField(default='basics')
    diagnostic_draft = models.JSONField(default=dict, blank=True)
    diagnostic_answers = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.user.username


class LessonContent(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=200)
    title_uz = models.CharField(max_length=200)
    summary = models.TextField(max_length=500)
    summary_uz = models.TextField(max_length=500)
    text = models.TextField()
    text_uz = models.TextField()
    hint = models.TextField()
    hint_uz = models.TextField()
    code = models.TextField(blank=True)
    minutes = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(180)])
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class TaskContent(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=200)
    title_uz = models.CharField(max_length=200)
    description = models.TextField(max_length=2000)
    description_uz = models.TextField(max_length=2000)
    requirements = models.JSONField(default=list)
    requirements_uz = models.JSONField(default=list)
    tag = models.CharField(max_length=40)
    priority = models.CharField(max_length=10, choices=[('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')])
    revision = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        from django.core.exceptions import ValidationError
        errors = {}
        for field in ('requirements', 'requirements_uz'):
            value = getattr(self, field)
            if not isinstance(value, list) or not 1 <= len(value) <= 30 or any(not isinstance(line, str) or not line.strip() or len(line) > 500 for line in value):
                errors[field] = 'Укажите от 1 до 30 непустых критериев, до 500 символов каждый.'
        if not errors and len(self.requirements) != len(self.requirements_uz):
            errors['requirements_uz'] = 'Количество критериев должно совпадать в обоих языках.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.pk:
            previous = type(self).objects.get(pk=self.pk)
            fields = ('title', 'title_uz', 'description', 'description_uz', 'requirements', 'requirements_uz', 'tag', 'priority')
            update_fields = kwargs.get('update_fields')
            compared = fields if update_fields is None else [field for field in fields if field in update_fields]
            changed = any(getattr(previous, field) != getattr(self, field) for field in compared)
            self.revision = previous.revision + int(changed)
            if changed and update_fields is not None:
                kwargs['update_fields'] = set(update_fields) | {'revision', 'updated_at'}
        return super().save(*args, **kwargs)


class ContentEdit(models.Model):
    kind = models.CharField(max_length=10, choices=[('lesson', 'Урок'), ('task', 'Задание')])
    slug = models.SlugField()
    author = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    before = models.JSONField()
    after = models.JSONField()
    changed_fields = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at', '-pk')

    def __str__(self):
        return f'{self.kind}: {self.slug}'


class LessonProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.SlugField()
    code = models.TextField(blank=True)
    completed = models.BooleanField(default=False)
    quiz_score = models.PositiveSmallIntegerField(null=True, blank=True)
    quiz_answers = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'lesson'], name='unique_user_lesson')]


class Submission(models.Model):
    STATUS_CHOICES = [('review', 'На проверке'), ('changes', 'Нужны изменения'), ('done', 'Принято')]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.SlugField()
    repository = models.URLField()
    commit = models.CharField(max_length=40, blank=True)
    description = models.TextField(max_length=1000)
    task_snapshot = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='review')
    reviewer = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_reviews')
    feedback = models.TextField(blank=True)
    score = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def task_title(self):
        from .catalog import TASKS
        return self.task_snapshot.get('title') or next((task['title'] for task in TASKS if task['slug'] == self.task), self.task)

    @property
    def task_title_uz(self):
        from .catalog import TASKS
        return self.task_snapshot.get('uz') or next((task['uz'] for task in TASKS if task['slug'] == self.task), self.task)

    @property
    def status_uz(self):
        return {'review': 'Tekshiruvda', 'changes': 'Tuzatish kerak', 'done': 'Qabul qilingan'}.get(self.status, self.status)


class SubmissionComment(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)


class SubmissionDraft(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.SlugField()
    repository = models.CharField(max_length=200, blank=True)
    commit = models.CharField(max_length=40, blank=True)
    description = models.TextField(max_length=1000, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'task'], name='unique_user_task_draft')]


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    text = models.TextField(blank=True)
    url = models.CharField(max_length=200, default='/dashboard/')
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class AIConversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=[('mentor', 'Mentor'), ('manager', 'Manager')])
    title = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)


class AIMessage(models.Model):
    conversation = models.ForeignKey(AIConversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=[('user', 'User'), ('assistant', 'Assistant')])
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class ChangeProposal(models.Model):
    STATUS_CHOICES = [('pending', 'Ожидает решения'), ('approved', 'Согласовано'), ('rejected', 'Нужно пересмотреть')]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.TextField(max_length=500, blank=True)
    hours = models.PositiveSmallIntegerField()
    days = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    feedback = models.TextField(blank=True, max_length=2000)
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_proposals')
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def clean(self):
        super().clean()
        if self.status != 'pending' and not self.feedback.strip():
            from django.core.exceptions import ValidationError
            raise ValidationError({'feedback': 'Объясните решение. / Qarorni tushuntiring.'})

    @property
    def status_uz(self):
        return {'pending': 'Qaror kutilmoqda', 'approved': 'Kelishildi', 'rejected': 'Qayta ko‘rib chiqish kerak'}[self.status]
