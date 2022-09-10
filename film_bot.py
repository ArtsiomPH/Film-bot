import os

import telebot
from telebot import types
import psycopg2 as db
import logging

#initialize bot
token = os.environ.get('TOKEN')
bot = telebot.TeleBot(token)

#connect to db
conn = db.connect(dbname=os.environ.get('DBNAME'), user=os.environ.get('USER'), password=os.environ.get('PASSWORD'),
                  host="localhost", port=5432)
cursor = conn.cursor()

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)

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


def add_serial(message):
    user_id = message.from_user.id
    cursor.execute(f"INSERT INTO serials(user_id, title) VALUES ('{user_id}', '{message.text}')")
    conn.commit()
    bot.send_message(message.chat.id, f'Название "{message.text}" добавлено')


# Запускаем бота
bot.infinity_polling(none_stop=True, interval=0)
