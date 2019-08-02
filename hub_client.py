import traceback

import aiohttp
import logging
import time
import asyncio
from functools import partial

from aiohttp import ClientWebSocketResponse

from db import DB
from hub import new_sub_message, hub_log, connect_hub, MESSAGE_TYPE


async def sub_topics(ws: ClientWebSocketResponse, topics):
    await ws.send_json(new_sub_message(topics))


async def on_message(ws, message: aiohttp.WSMessage):
    """
    {
      "message": {
        "data": "hello",
        "type": "PLAIN"
      },
      "topic": "global",
      "type": "MESSAGE"
    }
    """
    from main import bot

    hub_log.info(message)
    msg = message.json()

    type = msg['type']
    if type == 'MESSAGE':
        topic = msg['topic']
        if topic:
            # render message
            innter_type = msg['message']['type']
            innter_data = msg['message']['data']

            body = ''
            parse_mode = None
            disable_preview = False

            if innter_type == MESSAGE_TYPE.PLAIN.name:
                body = innter_data
            elif innter_type == MESSAGE_TYPE.MARKDOWN.name:
                body = innter_data
                parse_mode = "Markdown"
            elif innter_type == MESSAGE_TYPE.HTML.name:
                body = innter_data
                parse_mode = "HTML"
                disable_preview = True
            elif innter_type == MESSAGE_TYPE.JSON.name:
                body = innter_data
                disable_preview = True
            else:
                hub_log.warning(f"unprocessed type {innter_type}")

            if body:
                body = f"# {topic}\n\n{body}"
                all_topics = DB.get_all_topics()
                for chat_id, topics in all_topics.items():
                    if topic in topics:
                        try:
                            await bot.send_message(
                                chat_id,
                                body,
                                parse_mode=parse_mode,
                                disable_web_page_preview=disable_preview,
                            )
                        except Exception as e:
                            traceback.print_exc()


def run_async_func_in_loop(future, loop):
    result = loop.run_until_complete(future)
    print(f"result of {future}: {result}")
    return result


async def before_receive(ws, topics):
    await sub_topics(ws, topics)


def run_forever(topics=None):
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.new_event_loop()

    # get all topics
    while True:
        if topics is None:
            topics = []
            all_topics = DB.get_all_topics()
            for ts in all_topics.values():
                topics += ts

        try:
            run_async_func_in_loop(
                connect_hub(on_message, partial(before_receive, topics=topics)), loop
            )
        except asyncio.TimeoutError as e:
            print(e)
            time.sleep(10)
        print('-' * 100)


def run_in_new_thread():
    try:
        import thread
    except ImportError:
        import _thread as thread
    thread.start_new_thread(run_forever, ())


if __name__ == '__main__':
    topics = ['hello']
    run_forever(topics)
