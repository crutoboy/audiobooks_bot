import threading
import time
import os
import json

import telebot
from telebot import types


config = json.load(open('config.json', encoding="utf-8"))
token, src_path, dst_path, root_path, admin_id, interval = config['token'], config['src_path'], config['dst_path'], config['root_path'], config['admin'], config['interval_in_minuts']
bot = telebot.TeleBot(token)
dict_with_active_catalogs = {}

os.chdir(root_path)


def create_markup (path: str) -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    files = os.listdir(f'{dst_path}/{path}')

    if files:
        for i in files:
            if os.path.isfile(f'{dst_path}/{path}/{i}'):
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
    catalog(message)


@bot.message_handler(commands=['catalog'])
def catalog(message):
    dict_with_active_catalogs.update([[message.from_user.id, '.']])
    bot.send_message(message.from_user.id,
    'Каталог',
    reply_markup=create_markup(dict_with_active_catalogs[message.from_user.id]))


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    try:
        path = dict_with_active_catalogs[message.from_user.id]
    except:
        path = '/'
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
    elif message.text[0] == '🔈' and os.path.isfile(f'{dst_path}/{path}/{message.text[2:]}'):
        bot.send_audio(message.from_user.id, open(f'{dst_path}/{path}/{message.text[2:]}', 'r').read())
    elif os.path.isdir(f'{dst_path}/{path}/{message.text}'):
        dict_with_active_catalogs.update([[message.from_user.id, f'{path}/{message.text}']])
        bot.send_message(message.from_user.id,
        message.text,
        reply_markup=create_markup(dict_with_active_catalogs[message.from_user.id]))


def start_interval_action (foo, interval_in_min: int) -> None:
    while True:
        foo()
        time.sleep(interval_in_min * 60)

def recursion_check_files(path: str = '') -> None:
    cur_src = f'{src_path}/{path}'
    cur_dst = f'{dst_path}/{path}'
    content_src = os.listdir(cur_src)

    if not os.path.isdir(cur_dst):
        os.mkdir(cur_dst)

    for i in content_src:
        if (os.path.isfile(f'{cur_src}/{i}')) and ((not os.path.isfile(f'{cur_dst}/{i}')) or (os.path.getmtime(f'{cur_src}/{i}') > os.path.getmtime(f'{cur_dst}/{i}'))):
            with open(f'{cur_dst}/{i}', 'w') as file:
                doc = bot.send_document(admin_id, open(f'{cur_src}/{i}', 'rb'))
                file.write(doc.audio.file_id)
        elif os.path.isdir(f'{cur_src}/{i}'):
            recursion_check_files(f'{path}/{i}')

    content_dst = os.listdir(cur_dst)
    for i in content_src:
        content_dst.remove(i)
    
    for i in content_dst:
        os.remove(f'{cur_dst}/{i}')

threading.Thread(target=start_interval_action, args=(recursion_check_files, interval)).start()


if __name__ == '__main__':
    bot.infinity_polling()