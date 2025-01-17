from typing import List, Tuple
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from aiogram import Bot
from src.db_management import DBConnector


class StatsNotifier:
    _instance = None

    def __new__(cls, bot: Bot):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__init__(bot)
            cls._instance.start()
        return cls._instance

    def __init__(self, bot: Bot):
        self.bot = bot
        self.db_connector = DBConnector()

    def start(self):
        self.scheduler = AsyncIOScheduler()
        self._schedule_tasks_for_all_users()
        self.scheduler.start()

    def _schedule_tasks_for_all_users(self):
        users = self._get_users_with_intervals()
        for telegram_id, interval_minutes in users:
            self.schedule_task_for_user(telegram_id, interval_minutes)

    def _get_users_with_intervals(self) -> List[tuple]:
        conn = self.db_connector.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, interval_minutes FROM scheduler WHERE interval_minutes IS NOT NULL")
        return cursor.fetchall()

    def schedule_task_for_user(self, telegram_id: int, interval_minutes: int):
        self.scheduler.add_job(
            self._send_statistics_to_user,
            trigger=IntervalTrigger(minutes=interval_minutes),
            args=(telegram_id,),
            name=f"Statistics Notification for {telegram_id}",
            id=f"stats_notifier_{telegram_id}",
            replace_existing=True,
        )

    def cancel_task_for_user(self, telegram_id: int):
        self.scheduler.remove_job(f"stats_notifier_{telegram_id}")
        conn = self.db_connector.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scheduler "
                       "WHERE user_id = ? ",
                       (telegram_id,))
        conn.commit()

    async def _send_statistics_to_user(self, telegram_id: int):
        stats = self._get_user_stats(telegram_id)
        if stats:
            correct_answers, incorrect_answers = stats
            message = (
                f"Статистика использования бота:\n"
                f"Корректные запросы: {correct_answers}\n"
                f"Некорректные запросы: {incorrect_answers}"
            )
        else:
            message = "Пока нет данных о вашей статистике."
        await self.bot.send_message(chat_id=telegram_id, text=message)

    def _get_user_stats(self, telegram_id: int) -> Tuple[int, int]:
        conn = self.db_connector.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT correct_num, incorrect_num FROM stats WHERE user_id = ?",
            (telegram_id,),
        )
        return cursor.fetchone()
