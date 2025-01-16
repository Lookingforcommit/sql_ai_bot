from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, BotCommand, KeyboardButton, ReplyKeyboardMarkup
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
        BotCommand(command="/register", description="Зарегистрироваться в системе"),
        BotCommand(command="/check_sql", description="Проверить корректность SQL-запроса"),
        BotCommand(command="/menu", description="Вывод меню")
        BotCommand(command="/quit", description="Завершить диалог с помощником"),
    ]
    await bot.set_my_commands(commands)


def register_middlewares():
    registration_router.message.middleware(RegistrationMiddleware())
    registration_router.message.middleware(LoggingMiddleware())
    router.message.middleware(LoggingMiddleware())


def create_main_keyboard():
    keyboard = [[
        KeyboardButton(text="Регистрация"),
        KeyboardButton(text="Проверка SQL-запроса")
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
    await message.answer("Введите ваше имя:")
    await state.set_state(RegisterStates.waiting_for_name)

@router.message(F.text == "/quit")
async def quit_conversation(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == SQLDialogStates.in_conversation.state:
        await state.clear()
        await message.answer("Диалог с помощником завершен. Используйте /check_sql для новой проверки запроса.")
    else:
        await message.answer("Вы не находитесь в режиме диалога с помощником.")

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


@registration_router.message(F.text.startswith("/check_sql"))
@registration_router.message(F.text.startswith("Проверка SQL-запроса"))
async def check_sql_command(message: Message):
    telegram_id = message.from_user.id
    conn = db_connector.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users "
                   "WHERE telegram_id = ?", (telegram_id,))
    sql_query = message.text[len("/check_sql "):].strip()
    if not sql_query:
        await message.answer("Пожалуйста, укажите SQL-запрос после команды, например: `/check_sql SELECT * FROM users`")
        return
    try:
        conn.execute(f"EXPLAIN {sql_query}")
        cursor.execute("UPDATE stats "
                       "SET correct_num = correct_num + 1 "
                       "WHERE user_id = ?", (telegram_id,))
        conn.commit()
        await message.answer("Ваш запрос корректен.")
    except OperationalError as e:
        cursor.execute("UPDATE stats "
                       "SET incorrect_num = incorrect_num + 1 "
                       "WHERE user_id = ?", (telegram_id,))
        conn.commit()
        await message.answer(f"Ошибка в запросе: {e}")
        ai_manager = AIManager()
        help_message = await ai_manager.get_sql_error_help(sql_query, str(e))
        await message.answer(f"Анализ ошибки:\n\n{help_message}")
        await state.update_data(
            initial_query=sql_query,
            error_message=str(e),
            message_history=[
                {
                    "role": "system",
                    "content": "Вы - эксперт SQL, который помогает исправлять ошибки в запросах."
                },
                {
                    "role": "user",
                    "content": f"Запрос: {sql_query}\nОшибка: {str(e)}"
                },
                {
                    "role": "assistant",
                    "content": help_message
                }
            ]
        )
        await state.set_state(SQLDialogStates.in_conversation)
        await message.answer(
            "Теперь вы можете задавать дополнительные вопросы. Для завершения диалога используйте /quit")


@router.message(SQLDialogStates.in_conversation)
async def handle_sql_conversation(message: Message, state: FSMContext):
    if message.text.startswith('/'):
        return

    ai_manager = AIManager()
    state_data = await state.get_data()
    message_history = state_data.get('message_history', [])

    # Добавляем новый вопрос пользователя в историю
    message_history.append({"role": "user", "content": message.text})

    try:
        # Получаем ответ от GigaChat
        response_text = await ai_manager.continue_dialogue(message_history)

        # Сохраняем ответ в историю
        message_history.append({"role": "assistant", "content": response_text})
        await state.update_data(message_history=message_history)

        await message.answer(response_text)
    except Exception as e:
        await message.answer(f"Произошла ошибка при обработке вашего вопроса: {e}")


@registration_router.message(F.text)
async def handle_unknown_message(message: Message):
    await message.answer("Не понимаю вашего сообщения. Пожалуйста, используйте доступные команды.")
