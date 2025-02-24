# Бот-линтер для SQL-запросов
Telegram-бот для проверки корректности SQL-запросов с интеллектуальным анализом ошибок на базе GigaChat API. Бот позволяет пользователям регистрироваться, выполнять SQL-запросы, проверять их и получать подробные объяснения обнаруженных ошибок.

## Возможности
- Система регистрации пользователей с полными данными (ФИО)
- Проверка корректности SQL-запросов через SQLite
- Интеллектуальный анализ ошибок с использованием GigaChat
- Интерактивный режим диалога для помощи с запросами
- Система периодической отправки статистики
- Логирование действий пользователей
- Система миграций базы данных

## Обработка ошибок
Бот включает комплексную обработку ошибок для:
- Неверного синтаксиса SQL (с детальным анализом через GigaChat)
- Проблем с подключением к базе данных
- Ошибок в процессе регистрации
- Проблем связи с GigaChat API
- Ошибок при работе планировщика задач

## Логирование
Все действия пользователей автоматически записываются в базу данных, включая:
- Отправленные сообщения
- Использованные команды
- Результаты проверок запросов (корректные/некорректные)
- События регистрации
- Настройки периодических уведомлений

## Системные требования
- Python 3.8 или выше
- SQLite3
- Токен Telegram бота
- Учетные данные GigaChat API

# Установка
1. Клонируйте репозиторий:
```bash
git clone https://github.com/Lookingforcommit/sql_ai_bot.git
cd <директория-проекта>
```

2. Создайте и активируйте виртуальное окружение:
```bash
python -m venv venv
```
Для Linux/MacOS:
```bash
source venv/bin/activate
```
Для Windows:
```bash
venv\Scripts\activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

## Настройка
1. Создайте файл `.env` в корневой директории проекта со следующими переменными:
```env
BOT_TOKEN=ваш_токен_telegram_бота
DB_PATH=путь_к_базе_данных.db
MIGRATIONS_DIR=путь_к_директории_миграций
GIGACHAT_API_KEY=ваш_ключ_gigachat_api
```

2. Создайте директорию `sqlite/data` для хранения базы данных.

3. Подготовьте директорию для миграций базы данных и добавьте SQL-файлы миграций. Файлы миграций должны быть названы в последовательном порядке (например, `001_initial.sql`, `002_add_users.sql`).

## Запуск бота
1. Запустите бота:
```bash
python main.py
```

# Руководство по использованию

## Доступные команды
- `/menu` - Вывести главное меню
- `/start` - Начать взаимодействие с ботом
- `/register` - Начать процесс регистрации
- `/check_sql` - Проверить SQL-запрос
- `/quit` - Завершить разговор с SQL-ассистентом
- `/stats` - Настроить периодические сообщения со статистикой
- `/stop_notifications` - Отменить периодическую отправку статистики

## Процесс регистрации
1. Отправьте команду `/register` или нажмите кнопку "Регистрация"
2. Следуйте инструкциям для ввода:
   - Фамилии
   - Имени
   - Отчества

## Проверка SQL-запросов
1. Используйте команду `/check_sql`, за которой следует ваш запрос:
```
/check_sql SELECT * FROM users WHERE id = 1
```
2. Бот выполнит:
   - Проверку синтаксиса через SQLite
   - Анализ ошибок через GigaChat при необходимости
   - Переход в интерактивный режим для дополнительной помощи
   - Обновление статистики пользователя

3. После получения анализа ошибки вы можете:
  - Задавать дополнительные вопросы об ошибке
  - Запрашивать разъяснения по синтаксису SQL
  - Получать предложения по улучшению запроса
  - Использовать `/quit` для завершения диалога

## Настройка периодических уведомлений
1. Используйте команду `/stats` или кнопку "Отправка статистики"
2. Выберите интервал отправки (1, 10, 15, 30 или 60 минут)
3. Для отмены используйте команду `/stop_notifications`

# Структура проекта
```
project/
├── src/
│   ├── ai_management.py    # Интеграция с GigaChat
│   ├── configs_management.py # Управление конфигурацией
│   ├── db_management.py    # Операции с базой данных
│   ├── handlers.py         # Обработчики Telegram бота
│   ├── middlewares.py      # Промежуточное ПО
│   └── periodic_messages.py # Управление периодическими сообщениями
├── main.py                 # Точка входа в приложение
├── requirements.txt        # Зависимости проекта
└── .env                    # Переменные окружения
```

# Скриншоты работы
## Запуск и прохождение регистрации
![Запуск и прохождение регистрации](https://github.com/user-attachments/assets/027cca86-6597-4470-a0b3-3f1b55bc6ace)

## Меню бота
![Меню бота](https://github.com/user-attachments/assets/23cd9482-4c29-409c-b89b-ad20ad7f7329)

## Проверка SQL-запроса
![Проверка SQL-запроса](https://github.com/user-attachments/assets/835df50c-f5ee-4991-8ed6-7e24b9d84b93)

## Диалог с ИИ
![Диалог с ИИ](https://github.com/user-attachments/assets/3b43d9b3-18d3-4e7a-b805-ab5d1ab0760c)

## Настройка периодических сообщений
![Настройка периодических сообщений](https://github.com/user-attachments/assets/773ddb71-7a42-4377-9d01-37808903c305)

## Получение периодических сообщений
![Получение периодических сообщений](https://github.com/user-attachments/assets/2475ad37-20a8-4731-b748-421cfabadda7)

## Структура БД
![Структура БД](https://github.com/user-attachments/assets/7796ea23-e3ed-44c3-a7fc-c30d80f642f1)

# Блок-схема
[sql_ai_bot.pdf](https://github.com/user-attachments/files/18455663/sql_ai_bot.pdf)






