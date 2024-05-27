from redis.asyncio import Redis
from database.database import async_engine, async_session_factory
from database.models import PsyUsersTable, Base
from datetime import datetime
import asyncio

#_______redis_________

# redis executor
async def execute_redis_command(redis_pool, command: str, *args, **kwargs):
    """ Выполняет указанную команду Redis с переданными аргументами.
    Args:
        command (str): Название команды Redis, например 'get', 'set', 'del' и т.д.
        args: Позиционные аргументы для команды.
        kwargs: Именованные аргументы для команды.
    """
    async with Redis.from_pool(connection_pool=redis_pool) as redis:
        try:
            # Динамически вызываем метод из объекта Redis
            method = getattr(redis, command)
            result = await method(*args, **kwargs)  # Выполнение команды с аргументами
            return result
        except AttributeError:
            print(f"Redis does not support '{command}' method.")
            return None
        except Exception as e:
            print(f"Error executing Redis command '{command}': {e}")
            return None
        
    # Примеры использования
    #print(await execute_redis_command('get', 'some_key'))   # Получение значения по ключу
    #print(await execute_redis_command('set', 'some_key', 'new_value'))  # Установка значения
    #print(await execute_redis_command('del', 'some_key'))  # Удаление ключа

#_______postgres_________

# postgres create tables
async def create_tables():
    async with async_engine.begin() as conn:
         await conn.run_sync(Base.metadata.drop_all)
         await conn.run_sync(Base.metadata.create_all)

# postgres insert_user_data (new)
async def insert_user_data(chat_id: int, remaining_sessions: int, unix_time_in_30_days: int, remaining_days: int):
    new_user = PsyUsersTable(
        id=chat_id, 
        remaining_sessions_count=remaining_sessions,
        unix_time_end=unix_time_in_30_days,
        remaining_days=remaining_days
        )    
    async with async_session_factory() as session:
        session.add(new_user)
        await session.commit()

# postgres get_user_data
async def get_user_data(chat_id: int):
    async with async_session_factory() as session:
        user_info = await session.get(PsyUsersTable, chat_id)
        return user_info

async def user_check(chat_id: int, current_unix_time: int):
    user_info = await get_user_data(chat_id)
    async with async_session_factory() as session:
        if user_info:
            user_info = await change_user_period(user_info, current_unix_time)
        else:
            unix_time_in_30_days = current_unix_time + 2592000  # + 30 days
            await insert_user_data(chat_id, 3, unix_time_in_30_days, 30)
            user_info = await get_user_data(chat_id)
        
        session.add(user_info)  # Добавляйте нового пользователя в сессию
        
        await session.commit()

    return user_info


# change_user_period
async def change_user_period(user_info, current_unix_time: int):
    unix_time_in_30_days = current_unix_time + 2592000 # + 30 days
    if current_unix_time < user_info.unix_time_end:
        user_info.remaining_days = (user_info.unix_time_end - current_unix_time) // (60*60*24) + 1

    else:
        user_info.remaining_days = 30
        user_info.unix_time_end = unix_time_in_30_days
        user_info.remaining_sessions_count = 3

    return user_info
    

#count chinging
async def change_user_session_count(user_info, current_unix_time: int):
    async with async_session_factory() as session:
        if user_info.remaining_sessions_count > 0:
            user_info.remaining_sessions_count = user_info.remaining_sessions_count - 1
            session.add(user_info)
            await session.commit()
        
        if current_unix_time > user_info.unix_time_end:
            user_info.remaining_days = 30
            user_info.unix_time_end = current_unix_time + 2592000 # + 30 days
            user_info.remaining_sessions_count = 4
            
        return user_info

#asyncio.run(create_tables())
#current_time, time_in_30_days = asyncio.run(time_creator())
#asyncio.run(insert_user_data(123456, 4, current_time, time_in_30_days))
#asyncio.run(execute_redis_command(pool, "hset", "tasks_0", 12345, "Задача"))

