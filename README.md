## Оглавление
- [Описание](#description)
- [Стек](#stack)
- [Команды для запуска](#run)
- [Автор](#author)

---
## Описание <a id=description></a>
Yatube - социальная сеть для публикации постов. Проект выполнен с использованием фреймворка [Django](https://www.djangoproject.com/), по MVT архитектуре. 
Написаны тесты для проверки работы сервиса (pytest, unittest).

В проекте реализованы следующие возможности:
- регистрация, авторизация с верификацией
- публикация статей (текст, картинка)
- комментирование записей других пользователей
- подписка на авторов статей
- смена и восстановление пароля через почту
- пагинация
- кеширование страниц

## Стек <a id=stack></a>

Python3, Django 2.2, unittest, SQlite3, Pillow, sorl-thumbnail

---
## Команды для запуска <a id=run></a>

Перед запуском необходимо склонировать проект:
```bash
HTTPS: git clone https://github.com/devlili/hw05_final.git
SSH: git clone git@github.com:devlili/hw05_final.git
```

Cоздать и активировать виртуальное окружение:
```bash
python -m venv venv
```
```bash
Linux: source venv/bin/activate
Windows: source venv/Scripts/activate
```

Установить зависимости из файла requirements.txt:
```bash
python3 -m pip install --upgrade pip
```
```bash
pip install -r requirements.txt
```

Выполнить миграции:
```bash
python3 manage.py migrate
```

Запустить проект:
```bash
python3 manage.py runserver
```
---
## Автор <a id=author></a>

Лилия Альмухаметова
