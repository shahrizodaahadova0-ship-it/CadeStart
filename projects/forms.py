from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import ChangeProposal, Profile, Submission, SubmissionDraft, TaskContent


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class AIQuestionForm(forms.Form):
    question = forms.CharField(max_length=4000, widget=forms.Textarea(attrs={'rows': 3, 'maxlength': 4000}))
    consent = forms.BooleanField()


class CommentForm(forms.Form):
    body = forms.CharField(max_length=2000, widget=forms.Textarea(attrs={'rows': 4, 'maxlength': 2000}))


class LessonCheckForm(forms.Form):
    def __init__(self, questions, language, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for index, question in enumerate(questions):
            answers = question.get('uz_answers', question['answers']) if language == 'uz' else question['answers']
            self.fields[f'answer_{index}'] = forms.ChoiceField(
                label=question.get('uz_title', question['title']) if language == 'uz' else question['title'],
                choices=[(str(i), answer) for i, answer in enumerate(answers)], widget=forms.RadioSelect,
            )


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)

    class Meta:
        model = Profile
        fields = ('first_name', 'email', 'language', 'timezone', 'weekly_hours', 'github', 'paused')
        widgets = {'weekly_hours': forms.Select(choices=[('3-5', '3–5'), ('5-10', '5–10'), ('10+', '10+')])}

    def clean_timezone(self):
        value = self.cleaned_data['timezone']
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise forms.ValidationError('Укажите часовой пояс, например Asia/Tashkent.')
        return value


class SubmissionForm(forms.ModelForm):
    requirements_checked = forms.BooleanField()
    tests_checked = forms.BooleanField()
    secrets_checked = forms.BooleanField()

    class Meta:
        model = Submission
        fields = ('repository', 'commit', 'description')
        widgets = {'description': forms.Textarea(attrs={'rows': 5, 'maxlength': 1000})}

    def clean_commit(self):
        value = self.cleaned_data['commit']
        if value and (len(value) < 7 or any(c not in '0123456789abcdefABCDEF' for c in value)):
            raise forms.ValidationError('Введите SHA коммита: от 7 до 40 шестнадцатеричных символов.')
        return value


class SubmissionDraftForm(forms.ModelForm):
    requirements_checked = forms.BooleanField(required=False)
    tests_checked = forms.BooleanField(required=False)
    secrets_checked = forms.BooleanField(required=False)

    class Meta:
        model = SubmissionDraft
        fields = ('repository', 'commit', 'description')
        widgets = {'description': forms.Textarea(attrs={'rows': 5, 'maxlength': 1000})}


class ProposalForm(forms.ModelForm):
    class Meta:
        model = ChangeProposal
        fields = ('question', 'hours', 'days')
        widgets = {'question': forms.Textarea(attrs={'rows': 3, 'maxlength': 500})}


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ('status', 'feedback', 'score')
        widgets = {'feedback': forms.Textarea(attrs={'rows': 5})}

    def clean(self):
        data = super().clean()
        if data.get('status') == 'changes' and not data.get('feedback', '').strip():
            self.add_error('feedback', 'Объясните, что нужно исправить. / Nimani tuzatish kerakligini yozing.')
        return data

    def clean_score(self):
        value = self.cleaned_data['score']
        if value is not None and value > 100:
            raise forms.ValidationError('Оценка должна быть от 0 до 100.')
        return value


class SubmissionAdminForm(ReviewForm):
    class Meta(ReviewForm.Meta):
        fields = ('reviewer', 'status', 'feedback', 'score')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['reviewer'].queryset = User.objects.filter(is_staff=True, is_active=True).exclude(pk=self.instance.user_id)


class RequirementListField(forms.Field):
    widget = forms.Textarea(attrs={'rows': 6})

    def prepare_value(self, value):
        return '\n'.join(value) if isinstance(value, list) else value

    def to_python(self, value):
        if not value:
            return []
        return [line.strip() for line in value.splitlines() if line.strip()]


class TaskContentForm(forms.ModelForm):
    requirements = RequirementListField(label='Критерии приёмки — по одному на строку')
    requirements_uz = RequirementListField(label='Qabul mezonlari — har bir satrda bitta')

    class Meta:
        model = TaskContent
        exclude = ('slug', 'revision', 'updated_at')
