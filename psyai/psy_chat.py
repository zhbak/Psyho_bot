from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory, RunnablePassthrough
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
#from psyai.redis_chat import RedisChatMessageHistory
from dotenv import load_dotenv
from database.database import redis_url
from database.orm import execute_redis_command
import redis.asyncio as redis
import os
from redis.asyncio import ConnectionPool, Redis
from database.config import redis_port, redis_host


import logging

logger = logging.getLogger(__name__)


# Функция последовательный смены задачи
async def dynamic_task_change(chat_id, redis_pool, tasks, llm_output):
    
    # tasks - список задач
    # llm_output - ответ AI
    # previus_task - начальная задача при первом вызове или предыдущая после смены

    # Создаём асинхронное соединение с Redis

    llm_output = llm_output.lower()

    if 'давай перейдём к основной части' in llm_output:
        await  execute_redis_command(redis_pool, "hset", "tasks", chat_id, f"{tasks[1]}")
    elif 'давай перейдём к подведению итогов' in llm_output:
        await execute_redis_command(redis_pool, "hset", "tasks", chat_id, f"{tasks[2]}")



# Тримминг и суммаризация чата
def summarize_messages(chain_input):
    
    stored_messages = chat_history.messages
    if len(stored_messages) <= 8: # 8 - количество элементов user-ai в истории чата, которые суммрутся
        return False
    
    summarization_prompt = ChatPromptTemplate.from_messages(
        [
            MessagesPlaceholder(variable_name="chat_history"),
            (
                "user",
                "Distill the above chat messages into a single summary message. Include as many specific details as you can.",
            ),
        ]
    )
    summarization_chain = summarization_prompt | chat

    # Суммирование истории чата за исключением последних двух сообщений (одного от AI и одного от user)
    summary_message = summarization_chain.invoke({"chat_history": stored_messages[:-2]})
    chat_history.clear()
    chat_history.add_message(summary_message)

    # Добавление двух последних сообщений AI и user (одного от AI и одного от user)
    for message in stored_messages[-2:]:
        chat_history.add_message(message)

    return True

def get_message_history(session_id: str, url: str) -> BaseChatMessageHistory:
    return RedisChatMessageHistory(session_id, url)

# Главная функция
async def psyho_chat(system_prompt, user_input, pool, chat_id, chat, redis_url):
    try:
        
        logger.info("Task extraction")
        # Выполняем асинхронный запрос HGET
        task = await execute_redis_command(pool, "hget", "tasks", chat_id)

        logger.info("Task extracted: %s", task)

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    f"{system_prompt}" + str(task),
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ]
        )

        chain = prompt | chat

        logger.info("Chaining formed")

        chain_with_message_history = RunnableWithMessageHistory(
                chain,
                lambda session_id: get_message_history(session_id, redis_url),
                input_messages_key="input",
                history_messages_key="chat_history"
            )
        
        logger.info("Chain_with_message_history formed")
        
    #    chain_with_summarization = (
    #        RunnablePassthrough.assign(messages_summarized=summarize_messages)
    #        | chain_with_message_history
    #    )
        
        logger.info("Starting ainvoke with input: %s", user_input)

        response = await chain_with_message_history.ainvoke(
                {"input": f"{user_input}"},
                config={"configurable": {"session_id": f"{chat_id}"}}
            ) 
        
        logger.info("Received response: %s", response)

        return response

    except Exception as e:
        logger.error("Error during ainvoke: %s", e)
        raise e

#ool = ConnectionPool(host=redis_host, port=redis_port, decode_responses=True)

if __name__ == '__main__':
    
    system_prompt = """Your role is a psychologist (Andrey Lobkovskiy). You are having a conversation with a client. The communication style is conversational. Be a friend to the client. Add emoji to text and dialog. Consider the following theses:
Show understanding and empathy towards the client's feelings. Create a safe and trustworthy atmosphere for open communication. Be a friend to the client and talk on a first-name basis. Help in identifying and achieving the user's goals by offering practical strategies. Stimulate self-analysis and reflection through open questions. Direct to additional supporting resources when necessary. Observe ethical boundaries, avoiding medical or legal advice. Do not repeat what the client said. Ask less than 3 questions.
To prevent deviations from the set topic in the responses, follow these theses:
Stay within your role, clearly defining the boundaries of the answers and services provided. Use a firm, but polite wording to refuse requests that are outside of your role. Suggest directions or resources for obtaining the requested information outside your competence. Maintain a professional and conversational tone of communication, emphasizing the seriousness and specialization of your role. If necessary, provide an explanation why certain requests cannot be completed within your role. Invite the user to clarify their request to provide the most relevant and useful information.
Current task:
"""
    
    tasks = (
    "Establish contact and create a safe atmosphere. Do not name yourself. Start by offering the client to talk about themselves and ask a name of the client. If the task is achieved, write in a veiled manner, but literally: 'давай перейдём к определению проблемы'",
    "Conduct a conversation in a casual style aimed at clarifying and defining the main problem the client seeks help with. Ask the client about their expectations for the session and the goals they wish to achieve. Use active listening and reflection to ensure understanding and agree on the direction for the session. Share a one short story related to the client's issue. If the task is achieved, state it in a veiled manner, but literally: 'давай перейдём к основной части сессии'",
    "Apply therapeutic techniques and methods for in-depth work on the client's issue. This may include: dialogue, situation analysis, working with emotions, using cognitive-behavioral tasks, or exploring internal conflicts. Remain attentive to the client's reaction and their readiness to work at this stage. If the task is achieved, state it in a veiled manner, but literally: 'давай перейдём к подведению итогов'",
    "Discuss with the client key points and insights gained during the session. Assist them in articulating how these discoveries can be applied in life, and develop specific steps or homework for further progress. Ensure that the client feels confident and motivated to apply new strategies. Request feedback from the client about the session and discuss what was helpful and what could be improved. Plan the next steps and, if necessary, arrange the next meeting. Conclude the session by affirming your support for the client and expressing gratitude for their participation and openness in the process. If the task is achieved, state it in a veiled manner, but literally: 'До следующей сессии!'"
)
    
    load_dotenv()
    open_ai_key = os.environ.get("MINDMENTORTEST_OPENAI_TOKEN")
    chat = ChatOpenAI(model="gpt-4-turbo-preview", openai_api_key=open_ai_key, temperature= .5)

    r = redis.Redis(host="localhost", port="6379", decode_responses=True)
    

    # Задаём переменные
    chat_id = "user"
    redis_url = "redis://localhost:6379"
    chat_history = RedisChatMessageHistory(session_id=f"{chat_id}", url=f"{redis_url}")
    print(f"{chat_history}")
    
    task = tasks[0]
    user_input = "Поприветствуй меня"

    # Ответ на первый user_input
    response = psyho_chat(system_prompt, user_input, task, chat_history, chat)
    print("Psy: ", response.content)

    # Цикл на чат
    while True:
        user_input = input("You: ")
        if user_input == "off" or len(chat_history.messages) >= 50:
            response = psyho_chat("Ты психолог. Попращайся. Напиши что время сессии истекло", "Попращайся со мной", task="", chat_history=ChatMessageHistory(), chat=chat)
            print("Psyho: ", response.content)
            r.delete(f"message_store:{chat_id}")
            break
        response = psyho_chat(system_prompt, user_input, task, chat_history, chat=chat)
        task = dynamic_task_change(tasks, response.content, task)
        print("Psyho: ", response.content)
        if "До следующей сессии!" in response.content:
            break