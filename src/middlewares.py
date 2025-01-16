from aiogram.types import Message
from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable

from src.db_management import DBConnector


class RegistrationMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        self.db_connector = DBConnector()

    async def __call__(self, handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
                       event: Message, data: Dict[str, Any]):
        telegram_id = event.from_user.id
        conn = self.db_connector.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id FROM users"
                       " WHERE telegram_id = ?", (telegram_id,))
        user = cursor.fetchone()
        if not user:
            await event.answer("Вы не зарегистрированы, заполните анкету")
            return
        return await handler(event, data)


class LoggingMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        self.db_connector = DBConnector()

    async def __call__(self, handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
                       event: Message,data: Dict[str, Any]):
        telegram_id = event.from_user.id
        user_message = event.text
        if user_message:
            conn = self.db_connector.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT telegram_id FROM users "
                           "WHERE telegram_id = ?", (telegram_id,))
            user = cursor.fetchone()
            if user:
                cursor.execute("INSERT INTO actions (message, timestamp, user_id) "
                               "VALUES (?, datetime('now'), ?)",
                               (user_message, telegram_id))
                conn.commit()
        return await handler(event, data)
