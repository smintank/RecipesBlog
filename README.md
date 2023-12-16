# Foodgram

## Описание:
Foodgram - это вебсайт для любителей готовить и делиться своими рецептами с другими людьми. 
Frontend - это одностраничное SPA-приложение, написанное на фреймворкe React, backend написан на Django Rest Framework. Разворачивается вебсайт на сервере при помощи Docker Compose. Настроены CI/CD через Github Actions. 

### Возможности:
При помощи этого сервиса пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Есть фильтрация по тегам. Пользователям сайта также будет доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд и возможность скачать его в формате PDF.

# Установка:

## Установка и настройка бэкенд-приложения:

### 1. Сделайте форк репозитория указав при создании имя главной ветки `master`

### 2. Клонируйте репозиторий и перейдите в директорию `backend` проекта foodgram. Создайте виртуальное окружение и активируйте его.
```shell
python3 -m venv venv

source venv/bin/activate
```
### 3. Установите зависимости из файла requirements.txt в виртуальное окружение Django:
```shell
pip install -r requirements.txt
```
### 4. Выполните миграции и создайте суперюзера из директории с файлом manage.py:

```
# Примените миграции.
python3 manage.py migrate

# Создайте суперпользователя.
python3 manage.py createsuperuser
```
### 5. Отредактируйте файл `.env` в директории backend/foodgram_backend следующим образом:
```dotenv
# ~/foodgram_backend/.env

# Postgres settings
POSTGRES_ENGINE=django.db.backends.postgresql
POSTGRES_USER=django_user
POSTGRES_PASSWORD=django_pass
POSTGRES_DB=django
DB_HOST=db
DB_PORT=5432

# Django settings
DEBUG=0 # 1 - True, 0 or removed - False
SECRET_KEY='pcxzjmm6p31bk+c$##k2@l%$*3g$s9(lp7dclwib6^c$0b0+h5'
ALLOWED_HOSTS='123.456.789.012 127.0.0.1 localhost yourewebsite.ru'

# Inner nginx settings
NGINX_HOST_PORT=8000
```
POSTGRES_USER - имя пользователя для Postgres

POSTGRES_PASSWORD - пароль для доступа к Postgres

Остальные параметры для Postgres можно оставить как есть

DEBUG - это параметр режима отладки. `0` - режим отладки выключен (False), `1` - включен (True). Не меняйте если не собираетесь заниматься отладкой бекэнда.

SECRET_KEY - это секретный ключ Django который можно сгенерировать [тут](https://djecrety.ir) или ввести свой.

ALLOWED_HOSTS - разрешенные адреса для доступа к бекенду. Для добавления своих IP адресов или присвоенных им доманных имен, добавьте их к существующим локальным адресам `127.0.0.1` и `localhost`.

NGINX_HOST_PORT - порт который будет слушать внутренний nginx

### 6. Соберите статику бэкенд-приложения:
```shell
python3 manage.py collectstatic
```

## Создание и загрузка контейнеров на Docker Hub

### 1. Загрузка образов на Docker Hub
Прежде чем загружать образы на Docker Hub, нужно аутентифицировать докер-демон. Выполните команду аутентификации:

```shell
docker login
# А можно сразу указать имя пользователя:
docker login -u username 
```

### 2. Собираем образы

```shell
# Создать образ (build); 
# присвоить образу имя и тег (-t); 
# Dockerfile взять в указанной директории.
docker build -t username/foodgram_backend:latest backend/
docker build -t username/foodgram_frontend:latest frontend/
docker build -t username/foodgram_gateway:latest nginx/ 
```

### Если у вас Mac на Apple Silicon (M1/M2):
```shell
docker buildx build --platform=linux/amd64 -t foodgram_backend:latest backend/
docker buildx build --platform=linux/amd64 -t foodgram_frontend:latest frontend/
docker buildx build --platform=linux/amd64 -t foodgram_gateway:latest nginx/ 
```

### 3. Загрузка образов в Docker Hub
```shell
docker push username/foodgram_backend
docker push username/foodgram_frontend
docker push username/foodgram_gateway 
```

#### Не забудьте заменить `username` на свой.


## Деплой

## 1. Настройкa .env

### 1. В директории `/home/<user>` создайте папку `foodgram`
```shell
cd
mkdir foodgram
cd foodgram
```
### 2. Создайте и заполните файл `.env`.
```shell
subo nano .env
```
Добавить в файл текст из ранее созданного локального файла .env, не забыв изменить параметр `DEBUG` на `0`

Пример заполнения можно найти в файле `.env_exemple` в корневой папке репозитория.

## 2. Настройка Github Actions
### 1. Перейдите в Settings репозитория
### 2. Выберите пункт `Secrets And Variables` -> `Actions` -> `New repository secret`
### 3. Добавьте следующие ключи:
```text
HOST - IP адрес сервера
USER - имя пользователя сервера
SSH_PASSPHRASE - секретая фраза для доступа к серверу по SSH
SSH_KEY - текст приватного SSH ключа
DOCKER_USERNAME - Логин от аккаунта Docker Hub
DOCKER_PASSWORD - Пароль от аккаунта Docker Hub
TELEGRAM_TOKEN - Токен телеграм бота для отправки уведомлений об успешном деплое
TELEGRAM_TO - ваш телеграм ID на который будут приходить уведомления
```

### 4. Изменить название образов из DockerHub на свои в файле `.github/workflows/main.yaml`
```yaml
...
  
    with:
      context: ./backend/
      push: true
      tags: username/foodgram_backend:latest # здесь

...

    with:
      context: ./frontend/
      push: true
      tags: username/foodgram_frontend:latest # здесь

...

    with:
      context: ./nginx/
      push: true
      tags: username/foodgram_gateway:latest # и здесь

...
```

## 3. Установка и настройка внешнего веб-сервера Nginx
### 1. Если Nginx ещё не установлен на удалённый сервер, установите его:
```shell
sudo apt install nginx -y
```

### 2. Запустите Nginx командой:
```shell
sudo systemctl start nginx
```

### 3. Отредактируйте файл `default` в директории `/etc/nginx/sites-enabled/default` добавив новый сервер:
Впишите свой ip и доменное имя в параметр `server_name`
```
server {
    server_name yoursite.com;

    location / {
        proxy_set_header Host $http_host;
        proxy_pass http://127.0.0.1:8080;
    }
}
```

### 4. Сохраните изменения в файле, закройте его и проверьте на корректность:
```shell
sudo nginx -t
```

### 5. Перезагрузите конфигурацию Nginx:
```shell
sudo systemctl reload nginx
```

### 6 Активируйте разрешение принимать запросы только на порты 80, 443 и 22:
```shell
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
```

### 7. Включите файрвол:
```shell
sudo ufw enable
```
В терминале выведется запрос на подтверждение операции. Введите `y` и нажмите `Enter`. 

### 8. Проверьте работу файрвола:
```shell
sudo ufw status
```

## Получение и настройка SSL-сертификата

### 1. Находясь на сервере, установите certbot, если он ещё не установлен:
```shell
sudo apt install snapd
sudo snap install core; sudo snap refresh core
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
```

### 2. Запустите certbot и получите SSL-сертификат. Для этого выполните команду:
```shell
sudo certbot --nginx
```

Далее система попросит вас указать электронную почту и ответить на несколько вопро- сов. Сделайте это.
Следующим шагом укажите имена, для которых вы хотели бы активировать HTTPS

### 3. Проверьте конфигурацию Nginx, и если всё в порядке, перезагрузите её.
```shell
sudo systemctl reload nginx
```

## Сделать коммит!
Запустится автоматическая загрузка и установка на сервер
