from .models import Profile, Notification
from django.conf import settings
from django.utils.translation import get_language


TRANSLATIONS = {
    'ru': {
        'home': 'Главная',
        'projects': 'Проекты',
        'about': 'О нас',
        'bot': '🤖 Бот',
        'login': 'Войти',
        'register': 'Регистрация',
        'profile': 'Профиль',
        'logout': 'Выйти',

        'hero_title': 'Учись. Создавай. Развивайся.',
        'hero_text': 'Изучай программирование через реальные проекты.',
        'search': 'Поиск проектов...',
        'categories': 'Категории',
        'popular_projects': 'Популярные проекты',

        'python': 'Python',
        'django': 'Django',
        'web': 'Веб-разработка',
        'telegram': 'Telegram-боты',
        'database': 'Базы данных',

        'back': '← Назад',
        'technologies': 'Технологии',
        'level': 'Уровень',
        'created': 'Создан',
        'copy_code': 'Копировать код',

        'ai_title': '🤖 Мини AI',
        'ai_text': 'Задай вопрос о программировании',

        'username': 'Имя пользователя',
        'email': 'Email',
        'password': 'Пароль',
        'confirm_password': 'Повторите пароль',
        'language': 'Язык',
        'save': 'Сохранить',
    },

    'uz': {
        'home': 'Bosh sahifa',
        'projects': 'Loyihalar',
        'about': 'Biz haqimizda',
        'bot': '🤖 Bot',
        'login': 'Kirish',
        'register': "Ro'yxatdan o'tish",
        'profile': 'Profil',
        'logout': 'Chiqish',

        'hero_title': "O'rgan. Yarat. Rivojlan.",
        'hero_text': "Haqiqiy loyihalar orqali dasturlashni o'rgan.",
        'search': 'Loyihalarni qidirish...',
        'categories': 'Kategoriyalar',
        'popular_projects': 'Mashhur loyihalar',

        'python': 'Python',
        'django': 'Django',
        'web': 'Web dasturlash',
        'telegram': 'Telegram botlar',
        'database': "Ma'lumotlar bazasi",

        'back': '← Orqaga',
        'technologies': 'Texnologiyalar',
        'level': 'Daraja',
        'created': 'Yaratilgan',
        'copy_code': 'Kodni nusxalash',

        'ai_title': '🤖 Mini AI',
        'ai_text': 'Dasturlash haqida savol ber',

        'username': 'Foydalanuvchi nomi',
        'email': 'Email',
        'password': 'Parol',
        'confirm_password': 'Parolni takrorlang',
        'language': 'Til',
        'save': 'Saqlash',
    }
}


def language_context(request):

    language = request.session.get('language', 'ru')

    if request.user.is_authenticated:
        try:
            language = request.user.profile.language
        except Profile.DoesNotExist:
            pass

    return {
        'lang': language,
        't': TRANSLATIONS.get(language, TRANSLATIONS['ru']),
        'LANGUAGE_CODE': language,
    }


def user_language(request):
    language = request.session.get('language', 'ru')

    if request.user.is_authenticated:
        try:
            language = request.user.profile.language
        except Profile.DoesNotExist:
            pass

    return {
        'unread_notifications': Notification.objects.filter(user=request.user, read=False).count() if request.user.is_authenticated else 0,
        'mail_is_console': settings.MAILERS['default']['BACKEND'].endswith('console.EmailBackend'),
        'LANGUAGE_CODE': language,
        'current_language': language,
        'uz': language == 'uz',
        'lang': language,
        't': TRANSLATIONS.get(language, TRANSLATIONS['ru']),
    }
