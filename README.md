# Exchange API

Exchange API — это RESTful API для обмена товарами, позволяющее пользователям регистрироваться, авторизоваться, создавать объявления, искать и фильтровать их, а также предлагать обмен. Проект построен на Django и Django REST Framework с использованием PostgreSQL в качестве базы данных для приложения и SQLite для тестов. API документирован с помощью Swagger (доступно по /swagger/).

## Требования

* Docker и Docker Compose (для запуска в контейнерах)
* Python 3.12 и PostgreSQL 14.3 (для локальной разработки без Docker)

## Установка и запуск 

### 1. Клонируйте репозиторий 
```shell
git clone https://github.com/dydyaaa/django-test.git
cd django-test
```

### 2. Настройте файл переменных окружения
```env
POSTGRES_PASSWORD=123456
POSTGRES_USER=admin
POSTGRES_DB=exchangeDB
```

### 3. Запустите проект 
```shell
docker-compose up --build -d
```

Это выполнит следующие действия:
* Построит Docker-образ для Django-приложения.
* Запустит контейнер PostgreSQL (exchangeDB).
* Применит миграции базы данных.
* Запустит Django-сервер на http://localhost:8000.

## Доступ к API

Откройте http://localhost:8000/swagger/ в браузере, чтобы просмотреть документацию API.

Основные эндпоинты:
-  POST /api/register/ — регистрация пользователя.
- POST /api/login/ — авторизация и получение токена.
- GET /api/ads/ — список объявлений (с фильтрацией и поиском).
- GET /api/exchange/ — список предложений обмена.

### Use case

#### Описание
Пользователь хочет зарегистрироваться в системе, авторизоваться, создать объявление о товаре для обмена и предложить обмен на товар другого пользователя. Этот сценарий включает следующие шаги:

* Регистрация нового пользователя (POST /api/register/).
* Создание объявления (POST /api/ads/).
* Поиск объявлений других пользователей (GET /api/ads/ с фильтрацией или поиском).
* Создание предложения обмена (POST /api/exchange/).

## Остановка

Чтобы остановить контейнеры:
```shell
docker compose stop
```
Чтобы удалить контейнеры :
```shell
docker compose down -v
```

## Запуск тестов
Тесты используют SQLite в памяти, поэтому PostgreSQL не требуется.
```shell
cd exchanging
python manage.py test ads
```

## Проверка покрытия кода
```shell
cd exchanging
coverage run manage.py test ads
coverage html
```
Отчет о покрытии будет в папке htmlcov/. Откройте index.html в браузере.
