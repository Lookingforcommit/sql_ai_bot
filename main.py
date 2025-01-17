import asyncio
from src.handlers import dp, bot, set_commands, register_middlewares
from src.periodic_messages import StatsNotifier


async def main():
    register_middlewares()
    await set_commands()
    stats_notifier = StatsNotifier(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
