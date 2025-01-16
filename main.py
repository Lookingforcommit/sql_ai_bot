import asyncio
from src.handlers import dp, bot, set_commands, register_middlewares


async def main():
    register_middlewares()
    await set_commands()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
