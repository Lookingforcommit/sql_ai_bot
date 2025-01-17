from sqlite3 import OperationalError
from typing import List

from aiogram import Bot, Dispatcher, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (Message, BotCommand, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup,
                           InlineKeyboardButton, CallbackQuery)
from apscheduler.jobstores.base import JobLookupError

from src.ai_management import AIManager
from src.configs_management import ConfigsManager
from src.db_management import DBConnector
from src.periodic_messages import StatsNotifier
from src.middlewares import RegistrationMiddleware, LoggingMiddleware

db_connector = DBConnector()
configs_manager = ConfigsManager()
bot = Bot(token=configs_manager.bot_token)
dp = Dispatcher(storage=MemoryStorage())
registration_router = Router()
router = Router()
dp.include_router(router)
dp.include_router(registration_router)


class RegisterStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_surname = State()
    waiting_for_patronymic = State()


class SQLDialogStates(StatesGroup):
    in_conversation = State()


async def set_commands():
    commands = [
        BotCommand(command="/start", description="Начать взаимодействие с ботом"),
        BotCommand(command="/menu", description="Вывод меню"),
        BotCommand(command="/register", description="Зарегистрироваться в системе"),
        BotCommand(command="/check_sql", description="Проверить корректность SQL-запроса"),
        BotCommand(command="/quit", description="Завершить диалог с помощником"),
        BotCommand(command="/stats", description="Настроить периодическую отправку статистики"),
        BotCommand(command="/stop_notifications", description="Отменить периодическую отправку статистики"),
    ]
    await bot.set_my_commands(commands)


def register_middlewares():
    registration_router.message.middleware(RegistrationMiddleware())
    registration_router.message.middleware(LoggingMiddleware())
    router.message.middleware(LoggingMiddleware())


def create_main_keyboard():
    keyboard = [[
        KeyboardButton(text="Регистрация"),
        KeyboardButton(text="Проверка SQL-запроса"),
        KeyboardButton(text="Отправка статистики"),
    ]]
    keyboard = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    return keyboard


@router.message(F.text == "/menu")
async def menu_command(message: Message):
    keyboard = create_main_keyboard()
    await message.answer("Меню", reply_markup=keyboard)


@router.message(F.text == "/start")
async def start_command(message: Message):
    keyboard = create_main_keyboard()
    telegram_id = message.from_user.id
    conn = db_connector.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users "
                   "WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    if user:
        await message.answer("Вы уже зарегистрированы! Используйте /check_sql для проверки запросов.",
                             reply_markup=keyboard)
    else:
        await message.answer("Добро пожаловать! Используйте /register для регистрации.",
                             reply_markup=keyboard)


@router.message(F.text == "/register")
@router.message(F.text == "Регистрация")
async def register_command(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    conn = db_connector.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users "
                   "WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    if user:
        await message.answer("Вы уже зарегистрированы!")
        return
    await message.answer("Введите вашу фамилию:")
    await state.set_state(RegisterStates.waiting_for_surname)


@router.message(RegisterStates.waiting_for_surname)
async def process_surname(message: Message, state: FSMContext):
    await state.update_data(surname=message.text)
    await message.answer("Введите ваше имя:")
    await state.set_state(RegisterStates.waiting_for_name)


@router.message(RegisterStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите ваше отчество:")
    await state.set_state(RegisterStates.waiting_for_patronymic)


@router.message(RegisterStates.waiting_for_patronymic)
async def process_patronymic(message: Message, state: FSMContext):
    user_data = await state.get_data()
    name = user_data["name"]
    surname = user_data["surname"]
    patronymic = message.text
    telegram_id = message.from_user.id
    conn = db_connector.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (name, surname, patronymic, telegram_id) "
        "VALUES (?, ?, ?, ?)",
        (name, surname, patronymic, telegram_id)
    )
    cursor.execute(
        "INSERT INTO stats (correct_num, incorrect_num, user_id) "
        "VALUES (?, ?, ?)",
        (0, 0, telegram_id)
    )
    conn.commit()
    await message.answer(f"Регистрация завершена! Добро пожаловать, {name}.")
    await state.clear()


def init_message_history(sql_query: str, exception: Exception, help_message: str) -> List[dict]:
    message_history = [
        {
            "role": "system",
            "content": "Вы - эксперт SQL, который помогает исправлять ошибки в запросах."
        },
        {
            "role": "user",
            "content": f"Запрос: {sql_query}\nОшибка: {str(exception)}"
        },
        {
            "role": "assistant",
            "content": help_message
        }
    ]
    return message_history


async def on_correct_sql_query(cursor, telegram_id: int, conn, message: Message):
    cursor.execute("UPDATE stats "
                   "SET correct_num = correct_num + 1 "
                   "WHERE user_id = ?", (telegram_id,))
    conn.commit()
    await message.answer("Ваш запрос корректен.")


async def on_incorrect_sql_command(cursor, telegram_id: int, conn, message: Message, sql_query: str,
                                   e: Exception, state: FSMContext):
    cursor.execute("UPDATE stats "
                   "SET incorrect_num = incorrect_num + 1 "
                   "WHERE user_id = ?", (telegram_id,))
    conn.commit()
    await message.answer(f"Ошибка в запросе: {e}")
    ai_manager = AIManager()
    help_message = await ai_manager.get_sql_error_help(sql_query, str(e))
    await message.answer(f"Анализ ошибки:\n\n{help_message}")
    await state.update_data(message_history=init_message_history(sql_query, e, help_message))
    await state.set_state(SQLDialogStates.in_conversation)
    await message.answer("Теперь вы можете задавать дополнительные вопросы. "
                         "Для завершения диалога используйте /quit")


@registration_router.message(F.text.startswith("/check_sql"))
@registration_router.message(F.text.startswith("Проверка SQL-запроса"))
async def check_sql_command(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    conn = db_connector.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users "
                   "WHERE telegram_id = ?", (telegram_id,))
    if message.text.startswith("/check_sql"):
        sql_query = message.text[len("/check_sql "):].strip()
    else:
        sql_query = message.text[len("Проверка SQL-запроса "):].strip()
    if not sql_query:
        await message.answer("Пожалуйста, укажите SQL-запрос после команды, например: `/check_sql SELECT * FROM users`")
        return
    try:
        conn.execute(f"EXPLAIN {sql_query}")
        await on_correct_sql_query(cursor, telegram_id, conn, message)
    except OperationalError as e:
        if "syntax error" not in str(e).lower():
            await on_correct_sql_query(cursor, telegram_id, conn, message)
            return
        await on_incorrect_sql_command(cursor, telegram_id, conn, message, sql_query, e, state)


@router.message(SQLDialogStates.in_conversation)
async def handle_sql_conversation(message: Message, state: FSMContext):
    if message.text == "/quit":
        await state.clear()
        await message.answer("Диалог с помощником завершен. Используйте /check_sql для новой проверки запроса.")
        return
    ai_manager = AIManager()
    state_data = await state.get_data()
    message_history = state_data.get('message_history', [])
    message_history.append({"role": "user", "content": message.text})
    try:
        response_text = await ai_manager.continue_dialogue(message_history)
        message_history.append({"role": "assistant", "content": response_text})
        await state.update_data(message_history=message_history)
        await message.answer(response_text)
    except Exception as e:
        await message.answer(f"Произошла ошибка при обработке вашего вопроса: {e}")


def create_interval_keyboard():
    intervals = [1, 10, 15, 30, 60]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{interval} минут", callback_data=f"interval_{interval}")]
            for interval in intervals
        ]
    )
    return keyboard


@registration_router.message(F.text == "/stats")
@registration_router.message(F.text == "Отправка статистики")
async def stats_command(message: Message):
    keyboard = create_interval_keyboard()
    await message.answer("Выберите интервал для получения статистики:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("interval_"))
async def set_interval(callback: CallbackQuery):
    interval_minutes = int(callback.data.split("_")[1])
    telegram_id = callback.from_user.id
    conn = db_connector.get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO scheduler (user_id, interval_minutes) "
                   "VALUES (:1, :2) "
                   "ON CONFLICT(user_id) DO UPDATE SET interval_minutes = :2",
                   (telegram_id, interval_minutes))
    conn.commit()
    stats_sender = StatsNotifier(bot)
    stats_sender.schedule_task_for_user(telegram_id, interval_minutes)
    await callback.message.edit_text(
        f"Интервал успешно сохранён. Вы будете получать статистику с этим интервалом."
    )


@registration_router.message(F.text.startswith("/stop_notifications"))
async def stop_notifications_command(message: Message):
    telegram_id = message.from_user.id
    try:
        stats_sender = StatsNotifier(bot)
        stats_sender.cancel_task_for_user(telegram_id)
        await message.answer("Периодическая отправка сообщений остановлена.")
    except JobLookupError:
        await message.answer("У вас нет активных периодических задач.")


@registration_router.message(F.text)
async def handle_unknown_message(message: Message):
    await message.answer("Не понимаю вашего сообщения. Пожалуйста, используйте доступные команды.")
