from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.utils.http import url_has_allowed_host_and_scheme
from django.http import HttpResponseRedirect
from .models import Project, Profile
from .forms import RegisterForm


def home(request):
    projects = Project.objects.all().order_by('-created_at')
    query = request.GET.get('q', '').strip()
    if query:
        projects = projects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
            | Q(technologies__icontains=query)
        )

    return render(request, 'projects/home.html', {
        'projects': projects,
        'query': query,
    })


def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)

    return render(request, 'projects/project_detail.html', {
        'project': project
    })


@transaction.atomic
def register_view(request):

    if request.user.is_authenticated:
        return redirect('profile')

    if request.method == 'POST':

        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        language = request.POST.get('language', 'ru')
        if language not in dict(Profile.LANGUAGE_CHOICES):
            language = 'ru'

        if not username or not password:
            return render(request, 'projects/register.html', {
                'error': 'Заполни все обязательные поля.'
            })

        if password != password2:
            return render(request, 'projects/register.html', {
                'error': 'Пароли не совпадают.'
            })

        if User.objects.filter(username=username).exists():
            return render(request, 'projects/register.html', {
                'error': 'Пользователь с таким именем уже существует.'
            })

        form = RegisterForm({
            'username': username, 'email': email or '',
            'password1': password, 'password2': password2,
        })
        if not form.is_valid():
            return render(request, 'projects/register.html', {'error': ' '.join(
                str(error) for errors in form.errors.values() for error in errors
            )})
        user = form.save()

        Profile.objects.update_or_create(user=user, defaults={'language': language})

        login(request, user)

        return redirect('onboarding')

    return render(request, 'projects/register.html')


def login_view(request):
    next_url = request.POST.get('next', '') if request.method == 'POST' else request.GET.get('next', '')
    if not url_has_allowed_host_and_scheme(next_url, {request.get_host()}, require_https=request.is_secure()):
        next_url = ''
    if request.user.is_authenticated:
        return HttpResponseRedirect(next_url) if next_url else redirect('dashboard')

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return HttpResponseRedirect(next_url) if next_url else redirect('dashboard')

        return render(request, 'projects/login.html', {
            'error': True, 'next_url': next_url,
        })

    return render(request, 'projects/login.html', {'next_url': next_url})


@login_required
def logout_view(request):

    logout(request)

    return redirect('home')


@login_required
def profile_view(request):

    profile, created = Profile.objects.get_or_create(
        user=request.user
    )

    return render(request, 'projects/profile.html', {
        'profile': profile
    })

def language_choice(request):
    language = (
        request.POST.get('language', 'ru')
        if request.method == 'POST' else request.GET.get('lang', 'ru')
    )

    if language not in ['ru', 'uz']:
        language = 'ru'

    if request.user.is_authenticated:
        profile, created = Profile.objects.get_or_create(
            user=request.user
        )
        profile.language = language
        profile.save()

    request.session['language'] = language

    next_url = request.META.get('HTTP_REFERER', '/')
    if not url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        next_url = '/'
    return redirect(next_url)
