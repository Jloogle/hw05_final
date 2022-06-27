# Описание 
Социальная сеть с возможностью публиковать свои записи, подписываться на авторов, оставлять комментарии

# Стек технологий

* Django==2.2.19
* pytz==2021.3
* sqlparse==0.4.2
# Порядок установки
1. Клонируйте репозиторий:
```
git clone git@github.com:Jloogle/hw05_final
```
2. Перейдите в директорию с проектом
3. Создайте файл .env, в котором укажите переменную окружения SECRET_KEY.
4. Создайте виртуальное окружение:
```
python -m venv venv
```
5. Активируйте виртуальное окружение:
```
для windows: source venv/Scripts/activate
для linux/Mac: source venv/bin/activate
```
6. Установите зависимости:
```
pip install -r requirements.txt
```
7. Выполните миграции:
```
python manage.py migrate
```
8. Запустите сервер Django:
```
python manage.py runserver
```

# Разработчик
Живов Игорь - https://github.com/Jloogle
