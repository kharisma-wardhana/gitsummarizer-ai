import asyncio
import logging

from aiogram import Bot, Dispatcher

from .bot import router
from .config import get_settings


async def _main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    s = get_settings()
    bot = Bot(token=s.telegram_bot_token)
    dp = Dispatcher()
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    logging.getLogger(__name__).info("Bot started, polling…")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(_main())
