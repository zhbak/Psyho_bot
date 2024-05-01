from database import orm, database

async def start_text_statistic(message):
    user_state = await orm.execute_redis_command(database.pool, "hget", "status", message.chat.id)
    user_info = await orm.user_check(message.chat.id, message.date)
    if user_state == "1":
        await orm.change_user_session_count(user_info)
    start_text = f"{message.chat.first_name}, добро пожаловать!\n\n\
Тебе доступны 3 бесплатные сессии на 30 дней с этого момента.\n\n\
🔸️После 30 дней количество сессий автоматически восстановится.\n\
🔸️Одновременно на балансе может быть не более 3-х сессий.\n\n\
Ты можешь купить дополнительные. Купленные сессии останутся на балансе даже по истечении 30 дней. Ты сможешь использовать их в любой момент.\n\n\
Твои возможности на данный момент:\n\
🔸Количество доступных сессий: {user_info.remaining_sessions_count}\n\
🔸Дней до конца периода: {user_info.remaining_days}\n\n\
Для общения с психологом AI нажми на 🛋️\n\n\
Для покупки дополнительных сессий нажми 💳 (скоро будет доступно)"
    return start_text
    
    
start_psy_chat_text = "🔸У тебя будет возможность написать 6 сообщений.\n\
🔸Для возврата к главному меню нажми ☰ или Menu > Главное меню\n\n\
Сессия начинается!"

pause_phrases = (
    "Понимаю 🤗",
    "Интересно ✍️",
    "Спасибо за то, что поделились этим 🙏",
    "Позвольте мне обдумать это 🤔",
    "Принято ✍️",
    "Слышу вас 👂",
    "Я вас понял ✍️",
    "Осмысливаю это 🤔",
    "Так, давайте подумаем 🤔",
    "Я ценю вашу откровенность 🙏",
)