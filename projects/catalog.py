"""Учебные материалы. Пользовательский прогресс хранится отдельно в базе."""

LESSONS = [
    {'slug': 'basics', 'title': 'Основы Python', 'uz': 'Python asoslari', 'level': 'L0', 'minutes': 10, 'summary': 'Переменные, числа, строки и первые программы.', 'text': 'Переменная хранит значение. Создайте переменную total со значением 20000. Используйте print(total), чтобы вывести результат.', 'code': 'total = 20000\nprint(total)', 'hint': 'Для присваивания значения используйте знак =.'},
    {'slug': 'collections', 'title': 'Списки и коллекции', 'uz': "Ro‘yxatlar va kolleksiyalar", 'level': 'L1', 'minutes': 15, 'summary': 'Храните несколько значений и работайте с ними вместе.', 'text': 'Список хранит упорядоченные значения. Индексация начинается с нуля. Функция len() возвращает количество элементов. Создайте список prices из значений 12000 и 8000.', 'code': 'prices = [12000, 8000]\nprint(len(prices))', 'hint': 'Элементы списка записываются в квадратных скобках.'},
    {'slug': 'functions', 'title': 'Работа с функциями', 'uz': 'Funksiyalar bilan ishlash', 'level': 'L1', 'minutes': 12, 'summary': 'Параметры, повторное использование кода и возвращаемые значения.', 'text': 'Функция объединяет действия под одним именем. Параметр принимает входные данные, а return возвращает результат. Напишите calculate_total(prices), которая возвращает сумму цен, включая 0 для пустого списка.', 'code': 'def calculate_total(prices):\n    # Верните сумму цен\n    pass', 'hint': 'Встроенная функция sum(prices) вычисляет сумму элементов списка.'},
    {'slug': 'errors', 'title': 'Обработка ошибок', 'uz': 'Xatolar bilan ishlash', 'level': 'L1', 'minutes': 16, 'summary': 'Исключения и понятные сообщения об ошибках.', 'text': 'try и except помогают обработать ожидаемые исключения. Не скрывайте все ошибки: указывайте конкретный тип, например ValueError. Прочитайте пример и отметьте урок после изучения.', 'code': 'try:\n    number = int("hello")\nexcept ValueError:\n    print("Введите число")', 'hint': 'ValueError возникает, когда значение нельзя преобразовать в нужный формат.'},
    {'slug': 'git', 'title': 'Git: ветки и изменения', 'uz': 'Git asoslari', 'level': 'L1', 'minutes': 18, 'summary': 'Сохраняйте изменения и готовьте код к совместной работе.', 'text': 'Создайте ветку git switch -c feature/cart. После изменения кода проверьте git diff, добавьте нужные файлы через git add и сохраните коммит. Перед слиянием запускайте тесты.', 'code': 'git switch -c feature/cart\ngit status\ngit diff', 'hint': 'Коммит должен описывать одно законченное изменение.'},
    {'slug': 'http', 'title': 'HTTP и REST API', 'uz': 'HTTP va REST API', 'level': 'L2', 'minutes': 20, 'summary': 'Запросы, ответы и коды состояния.', 'text': 'GET получает данные, POST создаёт ресурс. Успешное создание обычно возвращает 201, ошибка данных — 400, отсутствие входа — 401. Опишите запрос создания заказа и ожидаемый ответ.', 'code': 'POST /api/orders/\nContent-Type: application/json\n\n{"items": [{"product_id": 1, "quantity": 2}]}', 'hint': 'Проверяйте права доступа до изменения данных.'},
    {'slug': 'database', 'title': 'Модели и база данных', 'uz': 'Modellar va ma’lumotlar bazasi', 'level': 'L2', 'minutes': 20, 'summary': 'Связи данных, ORM и миграции.', 'text': 'Модель описывает данные. ForeignKey связывает записи, а миграции сохраняют историю изменения схемы. Для заказов храните владельца и фильтруйте выборку по request.user.', 'code': 'Order.objects.filter(user=request.user)', 'hint': 'Проверяйте, что пользователь видит только свои заказы.'},
    {'slug': 'testing', 'title': 'Тестирование проекта', 'uz': 'Loyihani testlash', 'level': 'L3', 'minutes': 25, 'summary': 'Проверяйте обычные случаи и границы поведения.', 'text': 'Для API проверьте успешный запрос, неверные данные и отказ в доступе. Запустите python manage.py test локально и приложите результат к решению.', 'code': 'python manage.py test', 'hint': 'Тест должен проверять результат, заметный пользователю.'},
]

TASKS = [
    {'slug': 'products', 'id': 'SHOP-01', 'title': 'API товаров', 'uz': 'Mahsulotlar API', 'description': 'Создайте список товаров и получение товара по ID.', 'tag': 'Backend', 'priority': 'Medium', 'requirements': ['GET /api/products/ возвращает список товаров.', 'Можно получить товар по ID.', 'Для неизвестного ID возвращается 404.']},
    {'slug': 'categories', 'id': 'SHOP-02', 'title': 'Фильтр категорий', 'uz': 'Kategoriya filtri', 'description': 'Добавьте фильтрацию товаров по категории.', 'tag': 'Backend', 'priority': 'Low', 'requirements': ['Фильтр принимает идентификатор категории.', 'Без фильтра возвращаются все доступные товары.', 'Для пустой категории возвращается пустой список.']},
    {'slug': 'orders', 'id': 'SHOP-03', 'title': 'Создание заказа', 'uz': 'Buyurtma yaratish', 'description': 'Разработайте API для создания заказа из товаров корзины пользователя.', 'tag': 'Backend', 'priority': 'High', 'requirements': ['Только вошедший пользователь может создать заказ.', 'Проверяются количество и остатки товаров.', 'Сохраняются товары, владелец и общая сумма.', 'Успешный запрос возвращает 201, неверные данные — 400.', 'Пользователь видит только собственные заказы.']},
    {'slug': 'cart', 'id': 'SHOP-04', 'title': 'Сумма корзины', 'uz': 'Savat summasini hisoblash', 'description': 'Реализуйте расчёт общей стоимости товаров в корзине.', 'tag': 'Python', 'priority': 'Medium', 'requirements': ['Функция calculate_total принимает список цен.', 'Возвращает сумму значений.', 'Для пустого списка возвращает 0.', 'Есть тесты обычного и пустого списка.']},
    {'slug': 'auth', 'id': 'SHOP-05', 'title': 'Права доступа', 'uz': 'Ruxsatlarni tekshirish', 'description': 'Проверьте авторизацию и доступ к личным данным.', 'tag': 'Backend', 'priority': 'High', 'requirements': ['Личные данные доступны после входа.', 'Заказы фильтруются по владельцу.', 'Тесты проверяют доступ другого пользователя.']},
]

QUESTIONS = [
    {'title': 'Списки', 'code': 'numbers = [2, 4, 6]\nprint(len(numbers))', 'answers': ['2', '3', '6', '12'], 'correct': '1'},
    {'title': 'Функции', 'code': 'def double(x):\n    return x * 2\n\nprint(double(4))', 'answers': ['4', '2', '8', 'None'], 'correct': '2'},
    {'title': 'Словари', 'code': 'user = {"name": "Abror"}\nprint(user["name"])', 'answers': ['name', 'Abror', 'user', 'Ошибка'], 'correct': '1'},
    {'title': 'Условия', 'code': 'x = 5\nprint(x > 3)', 'answers': ['True', 'False', '5', '3'], 'correct': '0'},
    {'title': 'HTTP', 'code': '# Какой метод обычно создаёт ресурс?', 'answers': ['GET', 'POST', 'HEAD', 'OPTIONS'], 'correct': '1'},
    {'title': 'Git', 'code': '# Какая команда показывает изменения в файлах?', 'answers': ['git status --help', 'git init', 'git diff', 'git clone'], 'correct': '2'},
]

QUESTIONS += [
    {'title': 'Переменные', 'code': 'total = 10\ntotal += 5\nprint(total)', 'answers': ['5', '10', '15', '105'], 'correct': '2'},
    {'title': 'Типы данных', 'code': 'print(type("42").__name__)', 'answers': ['int', 'str', 'float', 'bool'], 'correct': '1'},
    {'title': 'Циклы', 'code': 'total = 0\nfor value in [1, 2, 3]:\n    total += value\nprint(total)', 'answers': ['3', '5', '6', '123'], 'correct': '2'},
    {'title': 'Исключения', 'code': '# Какой тип исключения вызывает int("hello")?', 'uz_code': '# int("hello") qanday istisno turini keltirib chiqaradi?', 'answers': ['ValueError', 'KeyError', 'IndexError', 'Нет ошибки / Xato yo‘q'], 'correct': '0'},
    {'title': 'База данных', 'code': '# Как выбрать только заказы текущего пользователя?', 'uz_code': '# Faqat joriy foydalanuvchi buyurtmalarini qanday tanlash mumkin?', 'answers': ['Order.objects.all()', 'Order.objects.filter(user=request.user)', 'Order.objects.first()', 'Order.objects.count()'], 'correct': '1'},
    {'title': 'Тестирование', 'code': '# Какой дополнительный случай важен для calculate_total(prices)?', 'uz_code': '# calculate_total(prices) uchun qaysi qo‘shimcha holat muhim?', 'answers': ['Только название файла / Faqat fayl nomi', 'Цвет редактора / Muharrir rangi', 'Пустой список / Bo‘sh ro‘yxat', 'Имя автора / Muallif ismi'], 'correct': '2'},
]
for question, lesson_slug in zip(QUESTIONS, [
    'collections', 'functions', 'collections', 'basics', 'http', 'git',
    'basics', 'basics', 'collections', 'errors', 'database', 'testing',
]):
    question['lesson'] = lesson_slug

UZ_LESSONS = {
    'basics': ('O‘zgaruvchilar, sonlar, satrlar va birinchi dasturlar.', 'O‘zgaruvchi qiymatni saqlaydi. 20000 qiymatli total o‘zgaruvchisini yarating. Natijani chiqarish uchun print(total) dan foydalaning.', 'Qiymat berish uchun = belgisidan foydalaning.'),
    'collections': ('Bir nechta qiymatni saqlang va ular bilan birga ishlang.', 'Ro‘yxat tartiblangan qiymatlarni saqlaydi. Indekslash noldan boshlanadi. len() elementlar sonini qaytaradi. 12000 va 8000 qiymatlaridan prices ro‘yxatini yarating.', 'Ro‘yxat elementlari kvadrat qavslar ichiga yoziladi.'),
    'functions': ('Parametrlar, kodni qayta ishlatish va qaytariladigan qiymatlar.', 'Funksiya amallarni bitta nom ostida birlashtiradi. Parametr kirish ma’lumotlarini qabul qiladi, return esa natijani qaytaradi. Narxlar summasini, bo‘sh ro‘yxat uchun esa 0 ni qaytaradigan calculate_total(prices) funksiyasini yozing.', 'sum(prices) ichki funksiyasi ro‘yxat elementlari summasini hisoblaydi.'),
    'errors': ('Istisnolar va tushunarli xato xabarlari.', 'try va except kutilgan istisnolarni qayta ishlashga yordam beradi. Barcha xatolarni yashirmang: aniq turni, masalan ValueError ni ko‘rsating. Misolni o‘qing va o‘rgangach darsni belgilang.', 'Qiymatni kerakli formatga o‘girib bo‘lmaganda ValueError yuz beradi.'),
    'git': ('O‘zgarishlarni saqlang va kodni jamoaviy ishga tayyorlang.', 'git switch -c feature/cart orqali branch yarating. Kod o‘zgargach git diff ni tekshiring, kerakli fayllarni git add orqali qo‘shing va commit saqlang. Merge oldidan testlarni ishga tushiring.', 'Commit bitta tugallangan o‘zgarishni tavsiflashi kerak.'),
    'http': ('So‘rovlar, javoblar va holat kodlari.', 'GET ma’lumotlarni oladi, POST resurs yaratadi. Muvaffaqiyatli yaratish odatda 201, noto‘g‘ri ma’lumot — 400, kirish yo‘qligi — 401 qaytaradi. Buyurtma yaratish so‘rovi va kutilgan javobni yozing.', 'Ma’lumotlarni o‘zgartirishdan oldin ruxsatlarni tekshiring.'),
    'database': ('Ma’lumotlar bog‘lanishi, ORM va migratsiyalar.', 'Model ma’lumotlarni tavsiflaydi. ForeignKey yozuvlarni bog‘laydi, migratsiyalar esa sxema o‘zgarishlari tarixini saqlaydi. Buyurtma egasini saqlang va so‘rovni request.user bo‘yicha filtrlang.', 'Foydalanuvchi faqat o‘z buyurtmalarini ko‘rishini tekshiring.'),
    'testing': ('Oddiy holatlar va chegaraviy xulqni tekshiring.', 'API uchun muvaffaqiyatli so‘rov, noto‘g‘ri ma’lumot va kirishni rad etishni tekshiring. python manage.py test ni lokal ishga tushiring va natijani yechimga qo‘shing.', 'Test foydalanuvchiga ko‘rinadigan natijani tekshirishi kerak.'),
}
for lesson in LESSONS:
    lesson['uz_summary'], lesson['uz_text'], lesson['uz_hint'] = UZ_LESSONS[lesson['slug']]

UZ_TASKS = {
    'products': ('Mahsulotlar ro‘yxati va ID orqali mahsulotni olish API sini yarating.', ['GET /api/products/ mahsulotlar ro‘yxatini qaytaradi.', 'Mahsulotni ID orqali olish mumkin.', 'Noma’lum ID uchun 404 qaytariladi.']),
    'categories': ('Mahsulotlarni kategoriya bo‘yicha filtrlashni qo‘shing.', ['Filtr kategoriya identifikatorini qabul qiladi.', 'Filtrsiz barcha mavjud mahsulotlar qaytariladi.', 'Bo‘sh kategoriya uchun bo‘sh ro‘yxat qaytariladi.']),
    'orders': ('Foydalanuvchi savatidagi mahsulotlardan buyurtma yaratish API sini ishlab chiqing.', ['Faqat kirgan foydalanuvchi buyurtma yarata oladi.', 'Mahsulot soni va ombor qoldig‘i tekshiriladi.', 'Mahsulotlar, egasi va umumiy summa saqlanadi.', 'Muvaffaqiyatli so‘rov 201, noto‘g‘ri ma’lumot 400 qaytaradi.', 'Foydalanuvchi faqat o‘z buyurtmalarini ko‘radi.']),
    'cart': ('Savatdagi mahsulotlarning umumiy narxini hisoblashni yarating.', ['calculate_total funksiyasi narxlar ro‘yxatini qabul qiladi.', 'Qiymatlar summasini qaytaradi.', 'Bo‘sh ro‘yxat uchun 0 qaytaradi.', 'Oddiy va bo‘sh ro‘yxat testlari mavjud.']),
    'auth': ('Autentifikatsiya va shaxsiy ma’lumotlarga kirishni tekshiring.', ['Shaxsiy ma’lumotlar kirgandan keyin ochiladi.', 'Buyurtmalar egasi bo‘yicha filtrlanadi.', 'Testlar boshqa foydalanuvchi kirishini tekshiradi.']),
}
for task in TASKS:
    task['uz_description'], task['uz_requirements'] = UZ_TASKS[task['slug']]

for question, title in zip(QUESTIONS, ['Ro‘yxatlar', 'Funksiyalar', 'Lug‘atlar', 'Shartlar', 'HTTP', 'Git', 'O‘zgaruvchilar', 'Ma’lumot turlari', 'Takrorlashlar', 'Istisnolar', 'Ma’lumotlar bazasi', 'Testlash']):
    question['uz_title'] = title
QUESTIONS[4]['uz_code'] = '# Qaysi metod odatda resurs yaratadi?'
QUESTIONS[5]['uz_code'] = '# Qaysi buyruq fayllardagi o‘zgarishlarni ko‘rsatadi?'
QUESTIONS[2]['uz_answers'] = ['name', 'Abror', 'user', 'Xato']
