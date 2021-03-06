import json
from hub import new_pub_message, run_util_close, MESSAGE_TYPE, http_post_data_to_hub, sub_topics

data = {"key": "value"}
topics = ["foo/bar"]


#  Websocket
def bee(ws):
    """
    the crawler
    """
    msg = new_pub_message(
        data,
        type=MESSAGE_TYPE.JSON.name,
        topics=topics
    )

    sub_topics
    ws.send(json.dumps(msg, ensure_ascii=False))


run_util_close(bee=bee)


# or HTTP
res = http_post_data_to_hub(data, topics)
print(res.json())
