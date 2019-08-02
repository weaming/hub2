#!/usr/bin/env python3
"""
Author       : weaming
Created Time : 2019-08-02 01:49:24
"""
import os
import logging
import sys

from aiogram import Bot, Dispatcher, executor, types

from db import DB
from hub_client import run_in_new_thread

logging.basicConfig(level=logging.INFO)
token = os.getenv('API_TOKEN')
if not token:
    print('missing API_TOKEN')
    sys.exit(1)
bot = Bot(token=token)
dp = Dispatcher(bot)
hub2_log = logging.getLogger("hub2")


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply(
        "Hi!\nI'm Hub2!\nTry /subscribe topic, separated by comma ',', spaces will be trimmed."
    )


def parse_topics(message):
    topics = [x.strip() for x in message.get_args().split(',') if x.strip()]
    cmd = message.get_command()
    user = message.from_user
    hub2_log.info("%s %s %s %s", cmd, user.id, user.full_name, topics)
    return str(user.id), user, topics


@dp.message_handler(commands=['subscribe', 'sub'])
async def subscribe(message: types.Message):
    chat_id, user, topics = parse_topics(message)
    new_topics = DB.add_chat_topics(chat_id, topics)
    await message.reply(f"Topics you subscribed now: {', '.join(new_topics)}")


@dp.message_handler(commands=['unsubscribe', 'unsub'])
async def unsubscribe(message: types.Message):
    chat_id, user, topics = parse_topics(message)
    new_topics = DB.remove_chat_topics(chat_id, topics)
    await message.reply(f"Topics you subscribed now: {', '.join(new_topics)}")


@dp.message_handler()
async def echo(message: types.Message):
    await bot.send_message(message.chat.id, message.text)


if __name__ == '__main__':
    run_in_new_thread()
    executor.start_polling(dp, skip_updates=True)
