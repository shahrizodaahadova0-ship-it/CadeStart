from .catalog import QUESTIONS


EXPLANATIONS = [
    ('len() возвращает количество элементов. В списке три элемента.', 'len() elementlar sonini qaytaradi. Ro‘yxatda uchta element bor.'),
    ('return возвращает x * 2: при x=4 результат равен 8.', 'return x * 2 ni qaytaradi: x=4 bo‘lsa, natija 8.'),
    ('Ключ name хранит строку Abror. user["name"] читает это значение.', 'name kaliti Abror satrini saqlaydi. user["name"] shu qiymatni o‘qiydi.'),
    ('5 больше 3, поэтому сравнение возвращает True.', '5 soni 3 dan katta, shuning uchun taqqoslash True qaytaradi.'),
    ('POST обычно используется для создания ресурса.', 'POST odatda resurs yaratish uchun ishlatiladi.'),
    ('git diff показывает изменения в файлах.', 'git diff fayllardagi o‘zgarishlarni ko‘rsatadi.'),
    ('Оператор += прибавляет 5 к исходному значению 10. Получается 15.', '+= operatori boshlang‘ich 10 qiymatga 5 qo‘shadi. Natija 15.'),
    ('Кавычки создают строку, поэтому тип значения "42" — str.', 'Qo‘shtirnoq satr yaratadi, shuning uchun "42" qiymat turi — str.'),
    ('Цикл складывает значения 1, 2 и 3. Сумма равна 6.', 'Sikl 1, 2 va 3 qiymatlarini qo‘shadi. Summa 6.'),
    ('Строку hello нельзя преобразовать в целое число. int() вызывает ValueError.', 'hello satrini butun songa aylantirib bo‘lmaydi. int() ValueError keltirib chiqaradi.'),
    ('filter(user=request.user) ограничивает выборку заказами текущего пользователя.', 'filter(user=request.user) tanlovni joriy foydalanuvchi buyurtmalari bilan cheklaydi.'),
    ('Пустой список — важный граничный случай. Для него функция должна вернуть 0.', 'Bo‘sh ro‘yxat — muhim chekka holat. Funksiya unga 0 qaytarishi kerak.'),
]


def questions_for(lesson):
    return [{**question, 'explanation': EXPLANATIONS[index][0], 'uz_explanation': EXPLANATIONS[index][1]}
            for index, question in enumerate(QUESTIONS) if question['lesson'] == lesson]
