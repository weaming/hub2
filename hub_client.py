import traceback

import aiohttp
import logging
import time
import asyncio

from aiohttp import ClientWebSocketResponse

from db import DB, Event
from hub import new_sub_message, hub_log, connect_hub, MESSAGE_TYPE


async def sub_topics(ws: ClientWebSocketResponse, topics):
    await ws.send_json(new_sub_message(topics))
    hub_log.info(f"subscribed {topics}")


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
            # ignore topic global
            if topic == 'global':
                return

            # render message
            innter_type = msg['message']['type']
            innter_data = msg['message']['data']

            body = ''
            parse_mode = None
            disable_preview = False
            disable_notification = False

            # parse message type
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
                all_topics = DB.get_key_topics_map()
                for key, topics in all_topics.items():

                    # reply in group or private chat
                    user_id, username, chat_id = Event.parse_key(key)
                    if user_id != chat_id:
                        real_body = f"@{username} {body}"
                        disable_notification = True
                    else:
                        real_body = body

                    if topic in topics:
                        try:
                            await bot.send_message(
                                chat_id,
                                real_body,
                                parse_mode=parse_mode,
                                disable_web_page_preview=disable_preview,
                                disable_notification=disable_notification,
                            )
                        except Exception as e:
                            traceback.print_exc()


def run_async_func_in_loop(future, loop):
    result = loop.run_until_complete(future)
    print(f"result of {future}: {result}")
    return result


async def after_msg(ws: ClientWebSocketResponse, msg: aiohttp.WSMessage):
    topics = DB.get_all_topics()

    # check extra topics subscribed
    upstream_topics = DB.get_upstream_topics()
    more = set(upstream_topics) - set(topics)
    # when subscribed more than 10 unused topics
    if len(more) > 10:
        await ws.close()
        DB.set_upstream_topics([])
        raise CloseException(str(more))

    upstream_topics = DB.get_upstream_topics()
    less = set(topics) - set(upstream_topics)
    if less:
        await sub_topics(ws, list(less))
        DB.set_upstream_topics(topics)


class CloseException(Exception):
    def __str__(self):
        return f"<CloseException: {repr(self)}>"


def run_forever():
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.new_event_loop()

    while True:
        try:
            run_async_func_in_loop(connect_hub(on_message, after_msg=after_msg), loop)
        except asyncio.TimeoutError as e:
            hub_log.warn(e)
            time.sleep(10)
        except CloseException as e:
            hub_log.info(e)
            hub_log.info('restarting...')


def run_in_new_thread():
    try:
        import thread
    except ImportError:
        import _thread as thread
    thread.start_new_thread(run_forever, ())


if __name__ == '__main__':
    run_forever()
