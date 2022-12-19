import os
import json

import telebot
from telebot import types


config = json.load(open('config.json', encoding="utf-8"))
token, root_path = config['token'], config['path_with_books']
bot = telebot.TeleBot(token)
dict_with_active_catalogs = {}

os.chdir(root_path)


def create_markup (path: str) -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    files = os.listdir(path)

    if files:
        for i in files:
            if os.path.isfile(f'{path}/{i}'):
                markup.add(types.KeyboardButton(f'🔈 {i}'))
            else:
                markup.add(types.KeyboardButton(i))
    else:
        markup.add(types.KeyboardButton('Пусто'))
    if path != '.':
        markup.add(types.KeyboardButton('↩Назад'))
        markup.add(types.KeyboardButton('🏠В начало'))

    return markup


@bot.message_handler(commands=['start', 'help'])
def start(message):
    bot.send_message(message.from_user.id,
'''Это бот для прослушывания аудио-книг
Ниже указан каталог книг, при внезапном его пропадании введите команду /start или /catalog''')


@bot.message_handler(commands=['catalog'])
def catalog(message):
    dict_with_active_catalogs.update([[message.from_user.id, '.']])
    bot.send_message(message.from_user.id,
    'Каталог',
    reply_markup=create_markup(dict_with_active_catalogs[message.from_user.id]))


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    path = dict_with_active_catalogs[message.from_user.id]
    if message.text[0] == '↩':
        dict_with_active_catalogs.update([[message.from_user.id, '/'.join(path.split('/')[:-1])]])
        bot.send_message(message.from_user.id,
        message.text,
        reply_markup=create_markup(dict_with_active_catalogs[message.from_user.id]))
    elif message.text[0] == '🏠':
        dict_with_active_catalogs.update([[message.from_user.id, '.']])
        bot.send_message(message.from_user.id,
        message.text,
        reply_markup=create_markup(dict_with_active_catalogs[message.from_user.id]))
    elif message.text[0] == '🔈' and os.path.isfile(f'{path}/{message.text[2:]}'):
        bot.send_audio(message.from_user.id, open(f'{path}/{message.text[2:]}', 'rb'))
    elif os.path.isdir(f'{path}/{message.text}'):
        dict_with_active_catalogs.update([[message.from_user.id, f'{path}/{message.text}']])
        bot.send_message(message.from_user.id,
        message.text,
        reply_markup=create_markup(dict_with_active_catalogs[message.from_user.id]))


if __name__ == '__main__':
    bot.infinity_polling()