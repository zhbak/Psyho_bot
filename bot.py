import asyncio, time
from bot_infrastucture import handlers, config
from database import orm
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния:
# start - 0
# psy_chat - 1


    
handlers.start_message(config.bot)
handlers.start_button_handler(config.bot)
handlers.psy_chat_handler(config.bot)



async def main():
    await orm.create_tables()
    await config.bot.polling(none_stop=True, interval=0, timeout=20)

"""
if __name__ == "__main__":
    print('Bot started.')
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Exception occurred: {e}")
"""



if __name__ == "__main__":
    print('Bot started.')
    while True:
        try:
            asyncio.run(main())
        except Exception as e:
            print(f"Exception occurred: {e}")
            time.sleep(15)  # Пауза перед следующей попыткой