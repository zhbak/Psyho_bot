from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import orm, database
from bot_infrastucture import buttons, texts
from psyai import prompts, psy_chat
from langchain_community.chat_message_histories import RedisChatMessageHistory
#from psyai.redis_chat import RedisChatMessageHistory
from bot_infrastucture import config
import random
import logging

logger = logging.getLogger(__name__)



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
        await bot.delete_message(chat_id=chat_id, message_id=call.message.message_id)
        if call.data == 'pushed_start_psychat_btn':
            user_state = await orm.execute_redis_command(database.pool, "hget", "status", call.message.chat.id) 
            logger.info("User state установлена: %s", user_state)
            user_info = await orm.user_check(call.message.chat.id, call.message.date)
            if user_state == "1":
                await orm.change_user_session_count(user_info, call.message.date) # Уменьшение количества сессий если клиент до этого был в psy_chat
            await orm.execute_redis_command(database.pool, "hset", "status", call.message.chat.id, 1) # Запись состояния 
            if await orm.execute_redis_command(database.pool, "exists", f"message_store:{chat_id}"):  # Проверка есть ли в Redis история с предыдущих сессий. Если да, удаляем.
                await orm.execute_redis_command(database.pool, "delete", f"message_store:{chat_id}")
            
            if user_info.remaining_sessions_count > 0: # Если есть доступные сессии
                await bot.send_message(chat_id=chat_id, text=texts.start_psy_chat_text)
                await orm.execute_redis_command(database.pool, "hset", "tasks", chat_id, f"{prompts.tasks[0]}") # Установка задачи для system_prompt
                logger.info("Задача установлена: %s", prompts.tasks[0])
                #RedisChatMessageHistory(session_id=f"{chat_id}", url = database.redis_url)
                user_input = f"Привет! Меня зовут {call.message.chat.first_name}. Поприветствуй меня на русском 👋"
                # Выполняем асинхронный запрос HGET
                logger.info("Запрос на ответ")
                response = await psy_chat.psyho_chat(prompts.system_prompt, user_input, database.pool, chat_id, config.chat, database.redis_url) # Ответ psychat на первый user_input
                await bot.send_message(chat_id, text=response.content, parse_mode="HTML")
                logger.info("Ответ на запрос получен")
                await psy_chat.dynamic_task_change(chat_id, database.pool, prompts.tasks, response.content)

            else:
                markup = InlineKeyboardMarkup()
                start_pay_btn = InlineKeyboardButton("💳", callback_data="pushed_start_pay_btn")
                markup = markup.add(start_pay_btn)
                await bot.send_message(chat_id, text="Твой лимит сессий исссяк.\n\nЧтобы купить сессии нажми 💳", reply_markup=markup)
                     
        elif call.data == 'pushed_start_pay_btn':
            await bot.send_message(chat_id=call.message.chat.id, text="Эта услуга пока не доступна 🔜", parse_mode="HTML")
        await bot.answer_callback_query(callback_query_id=call.id) 



def psy_chat_handler(bot):
    @bot.message_handler(func=lambda message: True)
    async def handle_messages(message):
        chat_id = message.chat.id
        user_status = await orm.execute_redis_command(database.pool, "hget", "status", chat_id)
        if user_status == "1":
            logger.info("Статус равен 1: %s", user_status)
            user_info = await orm.get_user_data(chat_id)
            
            logger.info("Оставшееся количество сессий: %s", user_info.remaining_sessions_count)
            if user_info.remaining_sessions_count > 0:
                chat_history = RedisChatMessageHistory(session_id=f"{chat_id}", url=f"{database.redis_url}")
                stored_messages = chat_history.messages
                message_count = len(stored_messages)
                last_message = stored_messages[-2]

                logger.info("Кол-во сообщений: %s", message_count)
                if message_count == 14: 
                    waiting_message = await bot.send_message(chat_id, random.choice(texts.pause_phrases), parse_mode="HTML", timeout=20)
                    await  orm.execute_redis_command(database.pool, "hset", "tasks", chat_id, f"{prompts.tasks[3]}")
                    response = await psy_chat.psyho_chat(system_prompt=prompts.system_prompt, user_input=message.text, pool=database.pool, chat_id=chat_id, chat=config.chat, redis_url=database.redis_url)
                    await bot.send_message(chat_id, text=response.content + "\n\nУ тебя осталось последнее сообщение в рамках сессии 😔", parse_mode="HTML")
                    await bot.delete_message(chat_id=chat_id, message_id=waiting_message.message_id)
                    await psy_chat.dynamic_task_change(chat_id, database.pool, prompts.tasks, response.content)

                elif message_count >= 16: 
                    waiting_message = await bot.send_message(chat_id, random.choice(texts.pause_phrases), parse_mode="HTML", timeout=20)
                    await  orm.execute_redis_command(database.pool, "hset", "tasks", chat_id, f"{prompts.tasks[4]}")
                    response = await psy_chat.psyho_chat(system_prompt=prompts.system_prompt, user_input=message.text, pool=database.pool, chat_id=chat_id, chat=config.chat, redis_url=database.redis_url)
                    await bot.send_message(chat_id, text=response.content + "\n\nСессия закончилась.\n\nПерейди в главное меню или нажми /start.", parse_mode="HTML")
                    await bot.delete_message(chat_id=chat_id, message_id=waiting_message.message_id)
                    await orm.execute_redis_command(database.pool, "hdel", "tasks", "chat_id") 
                    await orm.execute_redis_command(database.pool, "delete", f"message_store:{chat_id}")            

                # elif len(chat_history.messages) <= 2:
                #     response = await psy_chat.psyho_chat(prompts.system_prompt, message.text, database.pool, chat_id, config.chat) 
                #     await psy_chat.dynamic_task_change(chat_id, database.pool, prompts.tasks, response.content)
                #     await bot.send_message(chat_id, text=response.content)

                elif "До следующей сессии!" in last_message:
                    await bot.send_message(chat_id, text="Сессия закончилась.\n\nПерейди в главное меню или нажми /start.", parse_mode="HTML")
                    await orm.execute_redis_command(database.pool, "hdel", "tasks", chat_id) 
                    await orm.execute_redis_command(database.pool, "delete", f"message_store:{chat_id}")    

                else:
                    waiting_message = await bot.send_message(chat_id, random.choice(texts.pause_phrases), parse_mode="HTML", timeout=10)
                    response = await psy_chat.psyho_chat(prompts.system_prompt, message.text, database.pool, chat_id, config.chat, database.redis_url)
                    await bot.send_message(chat_id, text=response.content, parse_mode="HTML")
                    await bot.delete_message(chat_id=chat_id, message_id=waiting_message.message_id)
                    await psy_chat.dynamic_task_change(chat_id, database.pool, prompts.tasks, response.content)
                    
            else:
               markup = InlineKeyboardMarkup()
               start_pay_btn = InlineKeyboardButton("💳", callback_data="pushed_start_pay_btn")
               markup = markup.add(start_pay_btn)
               await bot.send_message(chat_id, text="Твой лимит сессий исссяк.\n\n Чтобы купить сессии нажми 💳", reply_markup=markup)
            
        else:
            await bot.send_message(chat_id=chat_id, text=f"Пока не знаю как ответить 👾\n\nПерейди в главное меню /start или напиши @zhbakov.", parse_mode="HTML")
