# hw05_final
Yatube. Учебный проект Яндекс.Практикум

## Описание:
Yatube - социальная сеть для публикации постов, где пользователи могут публиковать свои посты,
комментировать записи других авторов, подписываться на других пользователей

## Используемые технологии:

* Python
* Django
* SQLite3
* Unittest

## Как запустить проект:

1. Клонируйте репозиторий: `git clone git@github.com:mai-teacher/hw05_final.git`

2. Перейдите в него в командной строке: `cd hw05_final`

3. Cоздайте и активируйте виртуальное окружение: `python -m venv venv`

* Если у вас Linux/macOS, введите: `source venv/bin/activate`

* Если у вас Windows, введите: `source venv/scripts/activate`

4. Обновите PIP: `python -m pip install --upgrade pip`

5. Установите зависимости из файла **requirements.txt**: `pip install -r requirements.txt`

6. Перейдите в папку проекта: `cd yatube`

7. Выполните миграции: `python manage.py migrate`

8. Создайте суперпользователя: `python manage.py createsuperuser`

9. Запустите проект: `python manage.py runserver`

10. После чего проект будет доступен по адресу http://localhost:8000/

## Как запустить тесты:

Из папки проекта yatube выполните: `python manage.py test -v2`

## Автор
[Александр Макеев](https://github.com/mai-teacher)
