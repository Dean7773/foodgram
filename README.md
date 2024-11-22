# Foodgram
## Описание проекта
«Фудграм» — это платформа, где пользователи могут делиться своими собственными рецептами, сохранять интересные рецепты других авторов в избранное и подписываться на их обновления. Для зарегистрированных пользователей доступен сервис «Список покупок», который позволяет составлять и загружать список ингредиентов, необходимых для приготовления блюд.

## Технологии
* Python 3.9
* Django
* Django REST Framework
* Docker
* Gunicorn
* Nginx
* PostgreSQL

### Запуск проекта:

## Развернуть на удаленном сервере:

**Клонировать репозиторий:**
```
git@github.com:Dean7773/foodgram.git
```
**Установить на сервере Docker и Docker Compose:**
```
sudo apt install curl                                   - установка утилиты для скачивания файлов
curl -fsSL https://get.docker.com -o get-docker.sh      - скачать скрипт для установки
sh get-docker.sh                                        - запуск скрипта
sudo apt-get install docker-compose-plugin              - последняя версия docker compose
```
**Скопировать на сервер файлы: docker-compose.production.yml, nginx**
```
scp docker-compose.production.yml nginx.conf username@IP:/home/username/

# username - имя пользователя на сервере
# IP - публичный IP сервера
```
**Создать и запустить контейнеры Docker, выполнить команду на сервере:**
```
sudo docker compose up -d
```
**Выполнить миграции:**
```
sudo docker compose exec backend python manage.py migrate
```
**Собрать статику:**
```
sudo docker compose exec backend python manage.py collectstatic --noinput
```
**Наполнить базу данных содержимым из файла ingredients.json:**
```
sudo docker compose exec backend python manage.py load_ingredients
```
**Создать суперпользователя:**
```
sudo docker compose exec backend python manage.py createsuperuser
```
**Для остановки контейнеров Docker:**
```
sudo docker compose down -v      - с их удалением
sudo docker compose stop         - без удаления
```
## Локальный запуск проекта:

**Склонировать репозиторий к себе**
```
git@github.com:Dean7773/foodgram.git
```

**В корне проекта создать и заполнить файл .env:**
```
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgrampassword
DB_NAME=foodgram
DB_HOST=db
DB_PORT=5432
SECRET_KEY='Ваш ключ из settings.py'
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
```

**Создать и запустить контейнеры Docker, использовать файл docker-compose.yml**

**После запуска проект будут доступен по адресу: http://localhost/**

**Документация будет доступна по адресу: http://localhost/api/docs/**

## Автор проекта:
*  [Динар Муллануров](https://github.com/Dean7773)