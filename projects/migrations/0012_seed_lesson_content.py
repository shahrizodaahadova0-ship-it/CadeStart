from django.db import migrations


ROWS = [{'slug': 'basics',
  'title': 'Основы Python',
  'title_uz': 'Python asoslari',
  'summary': 'Переменные, числа, строки и первые программы.',
  'summary_uz': 'O‘zgaruvchilar, sonlar, satrlar va birinchi dasturlar.',
  'text': 'Переменная хранит значение. Создайте переменную total со значением 20000. Используйте '
          'print(total), чтобы вывести результат.',
  'text_uz': 'O‘zgaruvchi qiymatni saqlaydi. 20000 qiymatli total o‘zgaruvchisini yarating. '
             'Natijani chiqarish uchun print(total) dan foydalaning.',
  'hint': 'Для присваивания значения используйте знак =.',
  'hint_uz': 'Qiymat berish uchun = belgisidan foydalaning.',
  'code': 'total = 20000\nprint(total)',
  'minutes': 10},
 {'slug': 'collections',
  'title': 'Списки и коллекции',
  'title_uz': 'Ro‘yxatlar va kolleksiyalar',
  'summary': 'Храните несколько значений и работайте с ними вместе.',
  'summary_uz': 'Bir nechta qiymatni saqlang va ular bilan birga ishlang.',
  'text': 'Список хранит упорядоченные значения. Индексация начинается с нуля. Функция len() '
          'возвращает количество элементов. Создайте список prices из значений 12000 и 8000.',
  'text_uz': 'Ro‘yxat tartiblangan qiymatlarni saqlaydi. Indekslash noldan boshlanadi. len() '
             'elementlar sonini qaytaradi. 12000 va 8000 qiymatlaridan prices ro‘yxatini yarating.',
  'hint': 'Элементы списка записываются в квадратных скобках.',
  'hint_uz': 'Ro‘yxat elementlari kvadrat qavslar ichiga yoziladi.',
  'code': 'prices = [12000, 8000]\nprint(len(prices))',
  'minutes': 15},
 {'slug': 'functions',
  'title': 'Работа с функциями',
  'title_uz': 'Funksiyalar bilan ishlash',
  'summary': 'Параметры, повторное использование кода и возвращаемые значения.',
  'summary_uz': 'Parametrlar, kodni qayta ishlatish va qaytariladigan qiymatlar.',
  'text': 'Функция объединяет действия под одним именем. Параметр принимает входные данные, а '
          'return возвращает результат. Напишите calculate_total(prices), которая возвращает сумму '
          'цен, включая 0 для пустого списка.',
  'text_uz': 'Funksiya amallarni bitta nom ostida birlashtiradi. Parametr kirish ma’lumotlarini '
             'qabul qiladi, return esa natijani qaytaradi. Narxlar summasini, bo‘sh ro‘yxat uchun '
             'esa 0 ni qaytaradigan calculate_total(prices) funksiyasini yozing.',
  'hint': 'Встроенная функция sum(prices) вычисляет сумму элементов списка.',
  'hint_uz': 'sum(prices) ichki funksiyasi ro‘yxat elementlari summasini hisoblaydi.',
  'code': 'def calculate_total(prices):\n    # Верните сумму цен\n    pass',
  'minutes': 12},
 {'slug': 'errors',
  'title': 'Обработка ошибок',
  'title_uz': 'Xatolar bilan ishlash',
  'summary': 'Исключения и понятные сообщения об ошибках.',
  'summary_uz': 'Istisnolar va tushunarli xato xabarlari.',
  'text': 'try и except помогают обработать ожидаемые исключения. Не скрывайте все ошибки: '
          'указывайте конкретный тип, например ValueError. Прочитайте пример и отметьте урок после '
          'изучения.',
  'text_uz': 'try va except kutilgan istisnolarni qayta ishlashga yordam beradi. Barcha xatolarni '
             'yashirmang: aniq turni, masalan ValueError ni ko‘rsating. Misolni o‘qing va '
             'o‘rgangach darsni belgilang.',
  'hint': 'ValueError возникает, когда значение нельзя преобразовать в нужный формат.',
  'hint_uz': 'Qiymatni kerakli formatga o‘girib bo‘lmaganda ValueError yuz beradi.',
  'code': 'try:\n    number = int("hello")\nexcept ValueError:\n    print("Введите число")',
  'minutes': 16},
 {'slug': 'git',
  'title': 'Git: ветки и изменения',
  'title_uz': 'Git asoslari',
  'summary': 'Сохраняйте изменения и готовьте код к совместной работе.',
  'summary_uz': 'O‘zgarishlarni saqlang va kodni jamoaviy ishga tayyorlang.',
  'text': 'Создайте ветку git switch -c feature/cart. После изменения кода проверьте git diff, '
          'добавьте нужные файлы через git add и сохраните коммит. Перед слиянием запускайте '
          'тесты.',
  'text_uz': 'git switch -c feature/cart orqali branch yarating. Kod o‘zgargach git diff ni '
             'tekshiring, kerakli fayllarni git add orqali qo‘shing va commit saqlang. Merge '
             'oldidan testlarni ishga tushiring.',
  'hint': 'Коммит должен описывать одно законченное изменение.',
  'hint_uz': 'Commit bitta tugallangan o‘zgarishni tavsiflashi kerak.',
  'code': 'git switch -c feature/cart\ngit status\ngit diff',
  'minutes': 18},
 {'slug': 'http',
  'title': 'HTTP и REST API',
  'title_uz': 'HTTP va REST API',
  'summary': 'Запросы, ответы и коды состояния.',
  'summary_uz': 'So‘rovlar, javoblar va holat kodlari.',
  'text': 'GET получает данные, POST создаёт ресурс. Успешное создание обычно возвращает 201, '
          'ошибка данных — 400, отсутствие входа — 401. Опишите запрос создания заказа и ожидаемый '
          'ответ.',
  'text_uz': 'GET ma’lumotlarni oladi, POST resurs yaratadi. Muvaffaqiyatli yaratish odatda 201, '
             'noto‘g‘ri ma’lumot — 400, kirish yo‘qligi — 401 qaytaradi. Buyurtma yaratish so‘rovi '
             'va kutilgan javobni yozing.',
  'hint': 'Проверяйте права доступа до изменения данных.',
  'hint_uz': 'Ma’lumotlarni o‘zgartirishdan oldin ruxsatlarni tekshiring.',
  'code': 'POST /api/orders/\n'
          'Content-Type: application/json\n'
          '\n'
          '{"items": [{"product_id": 1, "quantity": 2}]}',
  'minutes': 20},
 {'slug': 'database',
  'title': 'Модели и база данных',
  'title_uz': 'Modellar va ma’lumotlar bazasi',
  'summary': 'Связи данных, ORM и миграции.',
  'summary_uz': 'Ma’lumotlar bog‘lanishi, ORM va migratsiyalar.',
  'text': 'Модель описывает данные. ForeignKey связывает записи, а миграции сохраняют историю '
          'изменения схемы. Для заказов храните владельца и фильтруйте выборку по request.user.',
  'text_uz': 'Model ma’lumotlarni tavsiflaydi. ForeignKey yozuvlarni bog‘laydi, migratsiyalar esa '
             'sxema o‘zgarishlari tarixini saqlaydi. Buyurtma egasini saqlang va so‘rovni '
             'request.user bo‘yicha filtrlang.',
  'hint': 'Проверяйте, что пользователь видит только свои заказы.',
  'hint_uz': 'Foydalanuvchi faqat o‘z buyurtmalarini ko‘rishini tekshiring.',
  'code': 'Order.objects.filter(user=request.user)',
  'minutes': 20},
 {'slug': 'testing',
  'title': 'Тестирование проекта',
  'title_uz': 'Loyihani testlash',
  'summary': 'Проверяйте обычные случаи и границы поведения.',
  'summary_uz': 'Oddiy holatlar va chegaraviy xulqni tekshiring.',
  'text': 'Для API проверьте успешный запрос, неверные данные и отказ в доступе. Запустите python '
          'manage.py test локально и приложите результат к решению.',
  'text_uz': 'API uchun muvaffaqiyatli so‘rov, noto‘g‘ri ma’lumot va kirishni rad etishni '
             'tekshiring. python manage.py test ni lokal ishga tushiring va natijani yechimga '
             'qo‘shing.',
  'hint': 'Тест должен проверять результат, заметный пользователю.',
  'hint_uz': 'Test foydalanuvchiga ko‘rinadigan natijani tekshirishi kerak.',
  'code': 'python manage.py test',
  'minutes': 25}]


def seed(apps, schema_editor):
    LessonContent = apps.get_model('projects', 'LessonContent')
    for row in ROWS:
        slug = row['slug']
        LessonContent.objects.using(schema_editor.connection.alias).get_or_create(slug=slug, defaults={key: value for key, value in row.items() if key != 'slug'})


class Migration(migrations.Migration):
    dependencies = [('projects', '0011_lessoncontent')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
