[![foodgramm](https://github.com/aleksey-vasilev/foodgram-project-react/actions/workflows/main.yml/badge.svg)](https://github.com/aleksey-vasilev/foodgram-project-react/actions/workflows/main.yml)

## Проект «Фудграм»

### Описание: 

Учебный прокт «Фудграм» (https://foodgramm.viewdns.net/recipes) — сайт, на котором пользователи могут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Пользователям сайта также доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

Предусмотрена регистрация пользователей и и возможность общения с базой через API.

Настроено развертывание через докер и CI/CD через GitHub Actions.

### Используемые технологии

![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?&style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/docker%20-%230db7ed.svg?&style=for-the-badge&logo=docker&logoColor=white)
![GitHub](https://img.shields.io/badge/github%20-%23121011.svg?&style=for-the-badge&logo=github&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/github%20actions%20-%232671E5.svg?&style=for-the-badge&logo=github%20actions&logoColor=white)

### Необходимые инструменты

* [Python](https://www.python.org/)
* [Pip](https://pypi.org/project/pip/)
* [Django](https://www.djangoproject.com/)
* [Docker](https://www.docker.com/)

### Установка:

1. Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/aleksey-vasilev/foodgram-project-react
cd foodgram-project-react
```

2. Создайть файл .env и заполнить его своими данными

```
POSTGRES_DB=...
POSTGRES_USER=...
POSTGRES_PASSWORD=...
DB_HOST=...
DB_PORT=..
USE_SQLITE=False/True (Предусмотрена возможность использования локальной базы SQLite)
```

3. Для установки docker compose на сервер, выполнить следующие действия:

```
sudo apt update
sudo apt install curl
curl -fSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
sudo apt-get install docker-compose-plugin
```

4. Перейти в директорию foodgram-project-react/ и запустить docker compose в режиме демона:

```
sudo docker compose -f docker-compose.yml up -d
```

5. Выполнить миграции и собрать статические файлы бэкенда в /backend_static/static/

```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
```
### В API доступны следующие эндпоинты (документация доступна по адресу /api/docs/):

* ```/api/users/```  Get-запрос – получение списка пользователей. POST-запрос – регистрация нового пользователя. Доступно без токена.

* ```/api/users/{id}``` GET-запрос – персональная страница пользователя с указанным id (доступно без токена).

* ```/api/users/me/``` GET-запрос – страница текущего пользователя. PATCH-запрос – редактирование собственной страницы. Доступно авторизированным пользователям. 

* ```/api/users/set_password``` POST-запрос – изменение собственного пароля. Доступно авторизированным пользователям. 

* ```/api/auth/token/login/``` POST-запрос – получение токена. Используется для авторизации по емейлу и паролю, чтобы далее использовать токен при запросах.

* ```/api/auth/token/logout/``` POST-запрос – удаление токена. 

* ```/api/tags/``` GET-запрос — получение списка всех тегов. Доступно без токена.

* ```/api/tags/{id}``` GET-запрос — получение информации о теге о его id. Доступно без токена. 

* ```/api/ingredients/``` GET-запрос – получение списка всех ингредиентов. Подключён поиск по частичному вхождению в начале названия ингредиента. Доступно без токена. 

* ```/api/ingredients/{id}/``` GET-запрос — получение информации об ингредиенте по его id. Доступно без токена. 

* ```/api/recipes/``` GET-запрос – получение списка всех рецептов. Возможен поиск рецептов по тегам и по id автора (доступно без токена). POST-запрос – добавление нового рецепта (доступно для авторизированных пользователей).

* ```/api/recipes/?is_favorited=1``` GET-запрос – получение списка всех рецептов, добавленных в избранное. Доступно для авторизированных пользователей. 

* ```/api/recipes/is_in_shopping_cart=1``` GET-запрос – получение списка всех рецептов, добавленных в список покупок. Доступно для авторизированных пользователей. 

* ```/api/recipes/{id}/``` GET-запрос – получение информации о рецепте по его id (доступно без токена). PATCH-запрос – изменение собственного рецепта (доступно для автора рецепта). DELETE-запрос – удаление собственного рецепта (доступно для автора рецепта).

* ```/api/recipes/{id}/favorite/``` POST-запрос – добавление нового рецепта в избранное. DELETE-запрос – удаление рецепта из избранного. Доступно для авторизированных пользователей. 

* ```/api/recipes/{id}/shopping_cart/``` POST-запрос – добавление нового рецепта в список покупок. DELETE-запрос – удаление рецепта из списка покупок. Доступно для авторизированных пользователей. 

* ```/api/recipes/download_shopping_cart/``` GET-запрос – получение текстового файла со списком покупок. Доступно для авторизированных пользователей. 

* ```/api/users/{id}/subscribe/``` GET-запрос – подписка на пользователя с указанным id. POST-запрос – отписка от пользователя с указанным id. Доступно для авторизированных пользователей

* ```/api/users/subscriptions/``` GET-запрос – получение списка всех пользователей, на которых подписан текущий пользователь Доступно для авторизированных пользователей. 

### Автор:

Алексей Васильев (aleksey-vasilev)
