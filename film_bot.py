import os

import telebot
import psycopg2 as db
import logging

from flask import Flask, request
from telebot import types

# initialize bot
TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)

# set logging
logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

# connect to db
DB_URI = os.getenv('DB_URI')
conn = db.connect(DB_URI, sslmode='require')
cursor = conn.cursor()

server = Flask(__name__)


@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id

    cursor.execute(f"INSERT INTO users VALUES ('{user_id}', '{message.from_user.username}') ON CONFLICT DO NOTHING;")
    conn.commit()

    bot.send_message(message.chat.id, f'Привет. Я фильм-бот, если тебе попался интересный фильм или сериал,'
                                f'и ты не хочешь забыть его название, можешь сказать его мне и я запомню. \n'
                                f'Напиши ОК, чтобы начать.')

    bot.register_next_step_handler(message, get_type_of_content)


@bot.message_handler(content_types=["button"])
def get_type_of_content(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    but1 = types.KeyboardButton(text='Фильмы')
    markup.add(but1)
    but2 = types.KeyboardButton(text='Сериалы')
    markup.add(but2)
    but3 = types.KeyboardButton(text='Посмотреть список фильмов')
    markup.add(but3)
    but4 = types.KeyboardButton(text='Посмотреть список сериалов')
    markup.add(but4)
    msg = 'Добавляйте новый фильм или сериал в ваш лист ожидания, либо просматривайте, что уже в него добавлено.'
    bot.send_message(message.chat.id, text=msg, reply_markup=markup)
    bot.register_next_step_handler(message, callback_worker)


@bot.message_handler(content_types=["text"])
def callback_worker(message):
    if message.text.strip() == 'Фильмы':
        answer = 'Введите название фильма!'
        bot.send_message(message.chat.id, answer)
        bot.register_next_step_handler(message, add_film)
    elif message.text.strip() == 'Сериалы':
        answer = 'Введите название сериала!'
        bot.send_message(message.chat.id, answer)
        bot.register_next_step_handler(message, add_serial)
    elif message.text.strip() == 'Посмотреть список фильмов':
        cursor.execute(f"SELECT title FROM films WHERE user_id = {message.from_user.id}")
        answer = "\n".join(list(str(*i) for i in cursor.fetchall()))
        bot.send_message(message.chat.id, answer)
    elif message.text.strip() == 'Посмотреть список сериалов':
        cursor.execute(f"SELECT title FROM serials WHERE user_id = {message.from_user.id}")
        answer = "\n".join(list(str(*i) for i in cursor.fetchall()))
        bot.send_message(message.chat.id, answer)


@bot.message_handler(content_types=["text"])
def add_film(message):
    user_id = message.from_user.id
    cursor.execute(f"INSERT INTO films(user_id, title) VALUES ('{user_id}', '{message.text}')")
    conn.commit()
    bot.send_message(message.chat.id, f'Название "{message.text}" добавлено')


@bot.message_handler(content_types=["text"])
def add_serial(message):
    user_id = message.from_user.id
    cursor.execute(f"INSERT INTO serials(user_id, title) VALUES ('{user_id}', '{message.text}')")
    conn.commit()
    bot.send_message(message.chat.id, f'Название "{message.text}" добавлено')


@server.route(f'/{TOKEN}', methods=['POST'])
def redirect_message():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "bot", 200


# Запускаем бота
if __name__ == '__main__':
    APP_URL = os.getenv('APP_URL')
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL)
    server.run(host="0.0.0.0", port=int(os.getenv('PORT', 5000)))
