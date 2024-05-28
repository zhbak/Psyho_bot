import asyncio
import time
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

# Основная асинхронная функция
async def main():
    await config.bot.polling(non_stop=True)

# Запуск бота
if __name__ == "__main__":
    logger.info("Bot started.")
    orm.create_tables()
    setup_handlers(config.bot)
    while True:
        try:
            asyncio.run(main())
        except Exception as e:
            logger.exception("Exception occurred: %s", e)
            time.sleep(5)  # Пауза перед следующей попыткой
