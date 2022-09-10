import os

import telebot
import psycopg2 as db
import logging

from flask import Flask, request
from telebot import types
from config import *

# initialize bot
bot = telebot.TeleBot(TOKEN)

server = Flask(__name__)

# connect to db
conn = db.connect(dbname=os.environ.get('DBNAME'), user=os.environ.get('USER'), password=os.environ.get('PASSWORD'),
                  host="localhost", port=5432)
cursor = conn.cursor()

logger = telebot.logger
logger.setLevel(logging.DEBUG)


@bot.message_handler(commands=["start"])
def start(m):
    user_id = m.from_user.id

    cursor.execute(f"INSERT INTO users VALUES ('{user_id}', '{m.from_user.username}') ON CONFLICT DO NOTHING;")
    conn.commit()

    bot.send_message(m.chat.id, f'Привет. Я фильм-бот, если тебе попался интересный фильм или сериал,'
                                f'и ты не хочешь забыть его название, можешь сказать его мне и я запомню. \n'
                                f'Напиши ОК, чтобы начать.')

    bot.register_next_step_handler(m, get_type_of_content)


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


@server.route(f'{TOKEN}', methods=["POST"])
def redirect_message():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return '!', 200


# Запускаем бота
# bot.infinity_polling(none_stop=True, interval=0)

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL)
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
