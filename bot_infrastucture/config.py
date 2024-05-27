import os
import telebot.async_telebot as telebot
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


load_dotenv()
bot_token = os.environ.get("MINDMENTORTEST_BOT_TOKEN")
bot = telebot.AsyncTeleBot(bot_token)
open_ai_key = os.environ.get("MINDMENTORTEST_OPENAI_TOKEN")
chat = ChatOpenAI(model="gpt-4-turbo", openai_api_key=open_ai_key, temperature= .35)