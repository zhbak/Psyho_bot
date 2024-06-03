import asyncio
#import time
import logging
from bot_infrastucture import handlers, config
from database import orm

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Инициализация обработчиков
def setup_handlers(bot):
    handlers.start_message(bot)
    handlers.start_button_handler(bot)
    handlers.psy_chat_handler(bot)

async def start_bot():
    setup_handlers(config.bot)
    await config.bot.infinity_polling(timeout=50, request_timeout=50, long_polling_timeout=10)

async def main():
    await orm.create_tables()
    while True:
        try:
            logger.info("Bot started.")
            await start_bot()
        except Exception as e:
            logger.exception("Exception occurred: %s", e)
            await asyncio.sleep(1)  # Пауза перед следующей попыткой

# Запуск бота
if __name__ == "__main__":
    asyncio.run(main())