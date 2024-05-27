import time, asyncio
from bot_infrastucture import handlers, config
from database.orm import create_tables


# создание таблиц в БД
asyncio.run(create_tables())


# Состояния:
# start - 0
# psy_chat - 1


    
handlers.start_message(config.bot)
handlers.start_button_handler(config.bot)
handlers.psy_chat_handler(config.bot)



async def main():
    await config.bot.polling()

if __name__ == "__main__":
    print('Bot started.')
    while True:
        try:
            asyncio.run(main())
        except Exception as e:
            print(f"Exception occurred: {e}")
            time.sleep(1)  # Пауза перед следующей попыткой