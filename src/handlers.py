from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, BotCommand
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from sqlite3 import OperationalError

from src.db_management import DBConnector
from src.configs_management import ConfigsManager
from src.middlewares import RegistrationMiddleware, LoggingMiddleware
from src.ai_management import AIManager

db_connector = DBConnector()
configs_manager = ConfigsManager()
bot = Bot(token=configs_manager.bot_token)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)


class RegisterStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_surname = State()
    waiting_for_patronymic = State()


async def set_commands():
    commands = [
        BotCommand(command="/start", description="Начать взаимодействие с ботом"),
        BotCommand(command="/register", description="Зарегистрироваться в системе"),
        BotCommand(command="/check_sql", description="Проверить корректность SQL-запроса"),
    ]
    await bot.set_my_commands(commands)


def register_middlewares():
    router.message.middleware(RegistrationMiddleware())
    router.message.middleware(LoggingMiddleware())


@router.message(F.text == "/start")
async def start_command(message: Message):
    telegram_id = message.from_user.id
    conn = db_connector.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    if user:
        await message.answer("Вы уже зарегистрированы! Используйте /check_sql для проверки запросов.")
    else:
        await message.answer("Добро пожаловать! Используйте /register для регистрации.")


@dp.message(F.text == "/register")
async def register_command(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    conn = db_connector.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    if user:
        await message.answer("Вы уже зарегистрированы!")
        return
    await message.answer("Введите ваше имя:")
    await state.set_state(RegisterStates.waiting_for_name)


@dp.message(RegisterStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите вашу фамилию:")
    await state.set_state(RegisterStates.waiting_for_surname)


@dp.message(RegisterStates.waiting_for_surname)
async def process_surname(message: Message, state: FSMContext):
    await state.update_data(surname=message.text)
    await message.answer("Введите ваше отчество:")
    await state.set_state(RegisterStates.waiting_for_patronymic)


@dp.message(RegisterStates.waiting_for_patronymic)
async def process_patronymic(message: Message, state: FSMContext):
    user_data = await state.get_data()
    name = user_data["name"]
    surname = user_data["surname"]
    patronymic = message.text
    telegram_id = message.from_user.id
    conn = db_connector.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (name, surname, patronymic, telegram_id) VALUES (?, ?, ?, ?)",
        (name, surname, patronymic, telegram_id)
    )
    conn.commit()
    await message.answer(f"Регистрация завершена! Добро пожаловать, {name}.")
    await state.clear()


@router.message(F.text.startswith("/check_sql"))
async def check_sql_command(message: Message):
    telegram_id = message.from_user.id
    conn = db_connector.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    sql_query = message.text[len("/check_sql "):].strip()

    if not sql_query:
        await message.answer("Пожалуйста, укажите SQL-запрос после команды, например: `/check_sql SELECT * FROM users`")
        return

    try:
        conn.execute(f"EXPLAIN {sql_query}")
        await message.answer("Ваш запрос корректен.")
    except OperationalError as e:
        await message.answer(f"Ошибка в запросе: {e}")
        ai_manager = AIManager()
        help_message = await ai_manager.get_sql_error_help(sql_query, str(e))
        await message.answer(f"Анализ ошибки:\n\n{help_message}")


@router.message(F.text)
async def handle_unknown_message(message: Message):
    await message.answer("Не понимаю вашего сообщения. Пожалуйста, используйте доступные команды.")
