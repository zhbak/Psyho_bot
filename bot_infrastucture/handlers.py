from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import orm, database
from bot_infrastucture import buttons, texts
from psyai import prompts, psy_chat
from langchain_community.chat_message_histories import RedisChatMessageHistory
from bot_infrastucture import config
import random



def start_message(bot):
    @bot.message_handler(commands=["start"])
    async def start(message):  
        
        chat_id = message.chat.id
        
        # Стартовое сообщение со статистикой
        # Записывает нового пользователя
        # Проверят старого
        # Выводит сообщение c кнопками перехода к psy_chat и оплаты
        await bot.send_message(chat_id, text = await texts.start_text_statistic(message), parse_mode="HTML", reply_markup= buttons.start_buttons())

        # Запись состояния в redis
        await orm.execute_redis_command(database.pool, "hset", "status", chat_id, 0)



def start_button_handler(bot):
    @bot.callback_query_handler(func=lambda call: True)
    async def query_handler(call):
        chat_id = call.message.chat.id
        if call.data == 'pushed_start_psychat_btn':
            user_state = await orm.execute_redis_command(database.pool, "hget", "status", call.message.chat.id) 
            user_info = await orm.user_check(call.message.chat.id, call.message.date)
            if user_state == "1":
                await orm.change_user_session_count(user_info, call.message.date) # Уменьшение количества сессий если клиент до этого был в psy_chat
            await orm.execute_redis_command(database.pool, "hset", "status", call.message.chat.id, 1) # Запись состояния 
            if await orm.execute_redis_command(database.pool, "exists", f"message_store:{chat_id}"):  # Проверка есть ли в Redis история с предыдущих сессий. Если да, удаляем.
                await orm.execute_redis_command(database.pool, "delete", f"message_store:{chat_id}")
            
            if user_info.remaining_sessions_count > 0: # Если есть доступные сессии
                await bot.send_message(chat_id=chat_id, text=texts.start_psy_chat_text)
                await orm.execute_redis_command(database.pool, "hset", "tasks", chat_id, f"{prompts.tasks[0]}") # Установка задачи для system_prompt
                await bot.send_message(chat_id, text="ок1", parse_mode="HTML")
                chat_history = RedisChatMessageHistory(session_id=f"{chat_id}", url=f"{database.redis_url}")
                await bot.send_message(chat_id, text="ок2", parse_mode="HTML")
                user_input = f"Привет! Меня зовут {call.message.chat.first_name}. Поприветствуй меня на русском 👋"
                await bot.send_message(chat_id, text="ок2.5", parse_mode="HTML")
                response = await psy_chat.psyho_chat(prompts.system_prompt, str(user_input), database.pool, chat_id, chat_history, config.chat) # Ответ psychat на первый user_input
                await bot.send_message(chat_id, text="ок3", parse_mode="HTML")
                await psy_chat.dynamic_task_change(chat_id, database.pool, prompts.tasks, response.content)
                await bot.send_message(chat_id, text="ок4", parse_mode="HTML")
                await bot.send_message(chat_id, text=response.content, parse_mode="HTML")

            else:
                markup = InlineKeyboardMarkup()
                start_pay_btn = InlineKeyboardButton("💳", callback_data="pushed_start_pay_btn")
                markup = markup.add(start_pay_btn)
                await bot.send_message(chat_id, text="Твой лимит сессий исссяк.\n\n Чтобы купить сессии нажми 💳", reply_markup=markup)
                     
        elif call.data == 'pushed_start_pay_btn':
            await bot.send_message(chat_id=call.message.chat.id, text="Эта услуга пока не доступна 🔜", parse_mode="HTML")
        await bot.answer_callback_query(callback_query_id=call.id) 



def psy_chat_handler(bot):
    @bot.message_handler(func=lambda message: True)
    async def handle_messages(message):
        chat_id = message.chat.id
        user_status = await orm.execute_redis_command(database.pool, "hget", "status", chat_id)
        if user_status == "1":
            user_info = await orm.get_user_data(chat_id)
            
            if user_info.remaining_sessions_count > 0:
                chat_history = RedisChatMessageHistory(session_id=f"{chat_id}", url=f"{database.redis_url}")
                stored_messages = chat_history.messages
                last_message = stored_messages[-2]

                if len(chat_history.messages) == 10: 
                    await bot.send_message(chat_id, random.choice(texts.pause_phrases), parse_mode="HTML")
                    response = await psy_chat.psyho_chat(system_prompt="Ты психолог. Подведи итоги сессии. Знай что следующим сообщением ты будешь прощаться с клиентом.", user_input=message.text, redis_pool=database.pool, chat_id=chat_id, chat_history=chat_history, chat=config.chat)
                    await psy_chat.dynamic_task_change(chat_id, database.pool, prompts.tasks, response.content)
                    await bot.send_message(chat_id, text=response.content + "\n\nУ тебя осталось последнее сообщение в рамках сессии 😔", parse_mode="HTML")

                elif len(chat_history.messages) >= 12: 
                    await bot.send_message(chat_id, random.choice(texts.pause_phrases), parse_mode="HTML")
                    response = await psy_chat.psyho_chat(system_prompt="Ты психолог. Попращайся.", user_input="Попращайся со мной", redis_pool=database.pool, chat_id=chat_id, chat_history=chat_history, chat=config.chat)
                    await bot.send_message(chat_id, text=response.content + "\n\nСессия закончилась.", parse_mode="HTML")
                    await orm.execute_redis_command(database.pool, "hdel", "tasks", "chat_id") 
                    await orm.execute_redis_command(database.pool, "delete", f"message_store:{chat_id}")            

                # elif len(chat_history.messages) <= 2:
                #     response = await psy_chat.psyho_chat(prompts.system_prompt, message.text, database.pool, chat_id, chat_history, config.chat) 
                #     await psy_chat.dynamic_task_change(chat_id, database.pool, prompts.tasks, response.content)
                #     await bot.send_message(chat_id, text=response.content)

                elif "До следующей сессии!" in last_message:
                    await bot.send_message(chat_id, text="Сессия закончилась.", parse_mode="HTML")
                    await orm.execute_redis_command(database.pool, "hdel", "tasks", chat_id) 
                    await orm.execute_redis_command(database.pool, "delete", f"message_store:{chat_id}")    

                else:
                    await bot.send_message(chat_id, random.choice(texts.pause_phrases), parse_mode="HTML")
                    response = await psy_chat.psyho_chat(prompts.system_prompt, message.text, database.pool, chat_id, chat_history, config.chat) 
                    await psy_chat.dynamic_task_change(chat_id, database.pool, prompts.tasks, response.content)
                    await bot.send_message(chat_id, text=response.content, parse_mode="HTML")

        else:
            await bot.send_message(chat_id=chat_id, text=f"Пока не знаю как ответить 👾", parse_mode="HTML")
