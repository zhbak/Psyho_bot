import telebot, os, time
from dotenv import load_dotenv
from old.buttons import buttons_creation
from psyai import psy_chat

# Подгрузка ключей
load_dotenv()
bot_token = os.environ.get("MINDMENTORTEST_BOT_TOKEN")
bot = telebot.TeleBot(bot_token)
user_selected_buttons = {}
user_status = {}
chat_messages = []

# Словарь с категориями и их соответствующими темами для обсуждения
categories = {
    "Моё состояние": ["Стресс", "Упадок сил", "Нестабильная самооценка", "Приступы страха и тревоги", "Перепады настроения", "Раздражительность", "Ощущение одиночества", "Проблемы с концентрацией", "Эмоциональная зависимость", "Проблемы со сном", "Расстройство пищевого поведения", "Панические атаки", " Навязчивые мысли о здоровье", "Сложности с алкоголем/накркотиками"],
    "Отношения": ["С партнёром", "В целом, с окружающими", "С родителями", "С детьми", "Сексуальные", "Сложности с ориентацией и её поиск"],
    "Работа, учёба": ["Недостаток мотивации", "Выгорание", "'Не знаю, чем хочу заниматься'", "Прокрастинация", "Отсутствие цели", "Смена, потеря работы"],
    "События в жизни": ["Переезд, эмиграция", "Беременность, Рождение ребёнка", "Разрыв отношений, развод", "Финансовые изменения", "Утрата близкого человека", "Болезнь, своя или близких", "Насилие"]
}

categories_keys = list(categories.keys())

@bot.message_handler(commands=['start'])
def start(message : telebot.types.Message):
    user_status[message.chat.id] = "Start"
    text = """
Привет, {}!\n
Выбери беспокоющие тебя темы в категориях, предложенных ниже.
Когда выберешь всё что хотел нажми 'Перейти к общению с психологом'.
""".format(message.from_user.first_name)
    bot.send_message(message.chat.id, text, reply_markup=buttons_creation(categories_keys, ["Перейти к общению с психологом"]))

# Обработчик сообщений
@bot.message_handler(func=lambda message: True)
def handle_messages(message, chat_messages = chat_messages):
    if message.chat.id not in user_selected_buttons:
        user_selected_buttons[message.chat.id] = {}

    if message.text == "Перейти к общению с психологом":
        user_status[message.chat.id] = "ChatGPT_conversation"
        assistant_massage, chat_messages = psy_chat.psyho_chat(user_selected_buttons[message.chat.id], message.text, message.chat.id, chat_messages, message.from_user.first_name)
        bot.send_message(message.chat.id, assistant_massage, reply_markup=telebot.types.ReplyKeyboardRemove())
        return chat_messages
    
    # Проверяем статус пользователя
    elif message.chat.id in user_status and user_status[message.chat.id] == 'ChatGPT_conversation':
        assistant_massage, chat_messages = psy_chat.psyho_chat(user_selected_buttons[message.chat.id], message.text, message.chat.id, chat_messages, message.from_user.first_name)
        bot.send_message(message.chat.id, assistant_massage)
        return chat_messages
    
    if message.text == "Вернуться к категориям":
        bot.send_message(message.chat.id, "Категории:", reply_markup=buttons_creation(categories_keys, ["Перейти к общению с психологом"]))

    category = None
    if message.text in categories_keys:
        # Сбрасываем статус ожидания для данного пользователя
        user_status[message.chat.id] = "Category_choosing"
        category = message.text
        themes = categories[category]
        continue_button_list = ["Вернуться к категориям", "Перейти к общению с психологом"]
        bot.send_message(message.chat.id, f"Темы для обсуждения в категории {category}\nНажми на интереусющие тебя темы.\nПовторное нажатие удаляет тему из твоего выбора.", reply_markup=buttons_creation(themes, continue_button_list))
    
    else:
        for cat, themes in categories.items():
            if message.text in themes:
                category = cat
                break

    if category is not None:
        if category not in user_selected_buttons[message.chat.id]:
            user_selected_buttons[message.chat.id][category] = []
    
        if message.text in user_selected_buttons[message.chat.id][category]:
            user_selected_buttons[message.chat.id][category].remove(message.text)
            bot.send_message(message.chat.id, "Выбрано:\n" + "\n".join(user_selected_buttons[message.chat.id][category]))

        elif message.text not in categories_keys:
            user_selected_buttons[message.chat.id][category].append(message.text)
            bot.send_message(message.chat.id, "Выбрано:\n" + "\n".join(user_selected_buttons[message.chat.id][category]))
    

if __name__ == "__main__":
    print('Bot started.')
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Exception occurred: {e}")
            time.sleep(15)  # Пауза перед следующей попыткой