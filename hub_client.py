import traceback

import aiohttp
import logging
import time
from io import BytesIO
import base64
import asyncio

from aiohttp import ClientWebSocketResponse

from db import DB, Event
from hub import new_sub_message, hub_log, connect_hub, MESSAGE_TYPE
from aiogram.types.base import InputFile


async def sub_topics(ws: ClientWebSocketResponse, topics):
    await ws.send_json(new_sub_message(topics))
    hub_log.info(f"subscribed {topics}")


def is_media(type):
    return type in [MESSAGE_TYPE.PHOTO.name, MESSAGE_TYPE.VIDEO.name]


async def on_message(ws, message: aiohttp.WSMessage):
    """
    {
      "message": {
        "data": "hello",
        "extended_data": [],
        "captions": [],
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
    by = 'by '
    if type == 'MESSAGE':
        topic = msg['topic']
        if topic:
            # ignore topic global
            if topic == 'global':
                return

            # render message
            innter_type = msg['message']['type']
            innter_data = msg['message']['data']
            extended_data = msg['message']['extended_data'] or []
            caption = msg['message']['caption']
            preview = msg['message']['preview']
            group = False

            body = ''
            parse_mode = None
            disable_preview = not preview
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
            elif innter_type == MESSAGE_TYPE.JSON.name:
                body = innter_data
            elif is_media(innter_type) or extended_data:
                body = [
                    {'type': innter_type, 'data': innter_data, 'caption': caption}
                ] + extended_data  # type: list
                print(body)
                # check: all types must be photo or video
                if not all(is_media(x['type']) for x in body):
                    hub_log.warning(f"not all types are media")
                    return
            else:
                hub_log.warning(f"unprocessed type {innter_type}")

            if body:
                body_with_topic = f"# {topic}\n\n{body}"
                all_topics = DB.get_key_topics_map()
                for key, topics in all_topics.items():
                    user_id, username, chat_id = Event.parse_key(key)

                    if topic in topics:
                        try:
                            if is_media(innter_type) or extended_data:
                                # string in hub message maybe a base64 encoded bytes
                                # or http url of a image
                                media_group = [
                                    {
                                        'type': x['type'].lower(),
                                        'media': x['data']
                                        if x['data'].startswith('http')
                                        else BytesIO(base64.b64decode(x['data'])),
                                        'caption': x['caption'],
                                    }
                                    for x in body
                                ]
                                if len(media_group) > 1:
                                    await bot.send_media_group(
                                        chat_id,
                                        media_group,
                                        disable_notification=disable_notification,
                                    )
                                else:
                                    if user_id != chat_id:
                                        caption_default = f"{by}{username} # {topic}"
                                    else:
                                        caption_default = f'# {topic}'
                                    if caption:
                                        caption_default += f' {caption}'

                                    x = media_group[0]
                                    if x['type'] == 'photo':
                                        await bot.send_photo(
                                            chat_id,
                                            x['media'],
                                            caption=caption_default,
                                            parse_mode=parse_mode,
                                            disable_notification=disable_notification,
                                        )
                                    else:
                                        await bot.send_video(
                                            chat_id,
                                            x['media'],
                                            caption=caption_default,
                                            parse_mode=parse_mode,
                                            disable_notification=disable_notification,
                                        )
                            else:
                                # reply in group or private chat
                                if user_id != chat_id:
                                    real_body = f"{by}{username} {body_with_topic}"
                                    disable_notification = True
                                else:
                                    real_body = body_with_topic

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


async def reset_upstream_topics(ws):
    DB.set_upstream_topics([])


async def sub_all(ws):
    topics = DB.get_all_topics()
    await sub_topics(ws, topics)


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

    # sync added topics
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
            run_async_func_in_loop(
                connect_hub(
                    on_message,
                    before_receive=sub_all,
                    after_msg=after_msg,
                    on_close=reset_upstream_topics,
                ),
                loop,
            )
        except asyncio.TimeoutError as e:
            hub_log.warning(e)
            time.sleep(10)
        except CloseException as e:
            hub_log.info(e)
        except Exception as e:  # catch all exceptions
            hub_log.info(e)

        DB.set_upstream_topics([])
        hub_log.info('restarting...')


def run_in_new_thread():
    try:
        import thread
    except ImportError:
        import _thread as thread
    thread.start_new_thread(run_forever, ())


if __name__ == '__main__':
    run_forever()
