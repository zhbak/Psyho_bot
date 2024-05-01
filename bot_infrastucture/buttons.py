from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def start_buttons():
    markup = InlineKeyboardMarkup()
    start_psychat_btn = InlineKeyboardButton("🛋️", callback_data="pushed_start_psychat_btn")
    start_pay_btn = InlineKeyboardButton("💳", callback_data="pushed_start_pay_btn")
    markup = markup.add(start_psychat_btn, start_pay_btn)
    return markup