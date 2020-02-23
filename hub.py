import aiohttp
import logging
import json
from copy import deepcopy
from typing import List, Dict
from enum import Enum
from base64 import b64encode

try:
    import thread
except ImportError:
    import _thread as thread
import requests

hub_log = logging.getLogger("hub")
hub_url = "wss://hub.drink.cafe/ws"


class MESSAGE_TYPE(Enum):
    PLAIN = "PLAIN"
    MARKDOWN = "MARKDOWN"
    JSON = "JSON"
    HTML = "HTML"
    PHOTO = "PHOTO"
    VIDEO = "VIDEO"


async def on_error(ws, error):
    hub_log.error(error)


async def on_close(ws):
    hub_log.info(f"websocket closed {ws}")


async def on_unknown(ws, msg):
    hub_log.info(f"unknown msg {msg}")


def data_to_str(data, type):
    if type in [MESSAGE_TYPE.JSON.name]:
        return json.dumps(data, ensure_ascii=False)
    if type in [MESSAGE_TYPE.PHOTO.name, MESSAGE_TYPE.VIDEO.name]:
        if not isinstance(data, str):
            return b64encode(data).encode('utf8')
    return str(data)


def new_pub_message(
    data,
    *,
    type=MESSAGE_TYPE.PLAIN.name,
    caption=None,
    topics=('global',),
    extended_data: List[Dict] = [],
):
    extended_data = deepcopy(extended_data)
    for x in extended_data:
        x['data'] = data_to_str(x['data'], x['type'])
    return {
        'action': "PUB",
        'topics': topics,
        'message': {
            'type': type,
            'data': data_to_str(data, type),
            'caption': caption,
            'extended_data': extended_data,
        },
    }


def new_sub_message(topics):
    return {'action': "SUB", "topics": topics}


def http_post_data_to_hub(data, topics):
    msg = new_pub_message(data, type=MESSAGE_TYPE.JSON.name, topics=topics)
    return requests.post("https://hub.drink.cafe/http", json=msg)


async def connect_hub(
    on_message, before_receive=None, after_msg=None, on_close=on_close, timeout=60
):
    timeout = aiohttp.ClientTimeout(total=timeout)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.ws_connect(hub_url, timeout=60 * 5, heartbeat=20) as ws:
            if before_receive:
                await before_receive(ws)
            async for msg in ws:  # type: aiohttp.WSMessage
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await on_message(ws, msg)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    await on_error(ws, msg)
                    break
                elif msg.type == aiohttp.WSMsgType.CLOSE:
                    await on_close(ws)
                    break
                else:
                    await on_unknown(ws, msg)

                if after_msg is not None:
                    await after_msg(ws, msg)
