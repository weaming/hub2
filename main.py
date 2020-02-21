#!/usr/bin/env python3
"""
Author       : weaming
Created Time : 2019-08-02 01:49:24
"""
import os
import json
import logging
import sys

from aiogram import Bot, Dispatcher, executor, types

from db import DB, Event
from hub_client import run_in_new_thread

logging.basicConfig(level=logging.INFO)
token = os.getenv('API_TOKEN')
if not token:
    print('missing API_TOKEN')
    sys.exit(1)
bot = Bot(token=token, proxy=os.getenv('https_proxy'))
dp = Dispatcher(bot)
hub2_log = logging.getLogger("hub2")


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply(
        "Hi!\nI'm Hub2!\nTry /subscribe topic, separated by comma ',', spaces will be trimmed."
    )


def parse_topics(message: types.Message):
    topics = [x.strip() for x in message.get_args().split(',') if x.strip()]
    cmd = message.get_command()
    user = message.from_user
    chat = message.chat
    hub2_log.info(
        "%s (%s %s) (%s %s) %s",
        cmd,
        user.id,
        user.full_name,
        chat.id,
        chat.type,
        topics,
    )
    event = Event(user, chat)
    # hub2_log.debug(event)
    return event, topics


@dp.message_handler(commands=['subscribe', 'sub'])
async def subscribe(message: types.Message):
    event, topics = parse_topics(message)
    new_topics = DB.add_chat_topics(event.key, topics)
    await message.reply(f"Topics you subscribed now: {', '.join(new_topics)}")


@dp.message_handler(commands=['unsubscribe', 'unsub'])
async def unsubscribe(message: types.Message):
    event, topics = parse_topics(message)
    new_topics = DB.remove_chat_topics(event.key, topics)
    await message.reply(f"Topics you subscribed now: {', '.join(new_topics)}")


@dp.message_handler(commands=['unsubscribe_all', 'unsub_all'])
async def unsubscribe_all(message: types.Message):
    event, topics = parse_topics(message)
    new_topics = DB.clear_chat_topics(event.key)
    await message.reply(f"Topics you subscribed now: {', '.join(new_topics)}")


@dp.message_handler(commands=['status'])
async def status(message: types.Message):
    event, topics = parse_topics(message)
    if event.user.username == os.getenv("ADMIN_NAME", 'weaming'):
        await message.reply(json.dumps(DB.get_key_topics_map(), ensure_ascii=False))
    else:
        await message.reply("You do not have permission.")


@dp.message_handler()
async def echo(message: types.Message):
    if message.text == '/ping':
        await bot.send_message(message.chat.id, f'chat_id: {message.chat.id}')
    else:
        await bot.send_message(message.chat.id, message.text)


if __name__ == '__main__':
    run_in_new_thread()
    executor.start_polling(dp, skip_updates=True)
