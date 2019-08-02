import logging
import time
import asyncio
from functools import partial

from aiohttp import ClientWebSocketResponse

from hub import new_sub_message, hub_log, connect_hub


async def sub_topics(ws: ClientWebSocketResponse, topics):
    await ws.send_json(new_sub_message(topics))


async def on_message(ws, message):
    hub_log.info(message)


def run_async_func_in_loop(future, loop):
    result = loop.run_until_complete(future)
    print(f"result of {future}: {result}")
    return result


async def before_receive(ws, topics):
    await sub_topics(ws, topics)


def run_forever(topics):
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    while True:
        try:
            run_async_func_in_loop(
                connect_hub(on_message, partial(before_receive, topics=topics)), loop
            )
        except asyncio.TimeoutError as e:
            print(e)
            time.sleep(10)
        print('-' * 100)


if __name__ == '__main__':
    topics = ['hello']
    run_forever(topics)
