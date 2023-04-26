"""
 @Author: jiran
 @Email: jiran214@qq.com
 @FileName: douyin.py
 @DateTime: 2023/4/25 21:56
 @SoftWare: PyCharm
"""
import asyncio
import time

import aiohttp

import json

from bilibili_api import sync

from src.events import DyDanmuMsgEvent, DyAttentionEvent, DySendGiftEvent, DyCkEvent, DyWelcomeWordEvent
from src.utils import user_queue


def msg(event_dict):
    event_dict['Data'] = json.loads(event_dict['Data'])
    event = DyDanmuMsgEvent(event_dict)
    user_queue.send(event)


def ck(event_dict):  # type2
    if not user_queue.event_queue.full():
        event_dict['Data'] = json.loads(event_dict['Data'])
        event = DyCkEvent(event_dict)
        # print("感谢" + load_data.get("Content"))
        user_queue.send(event)


def welcome(event_dict):  # type3
    if not user_queue.event_queue.full():
        event_dict['Data'] = json.loads(event_dict['Data'])
        event = DyWelcomeWordEvent(event_dict)
        # print("欢迎:" + json2["Nickname"])
        user_queue.send(event)


def Gift(event_dict):  # type5
    event_dict['Data'] = json.loads(event_dict['Data'])
    event = DySendGiftEvent(event_dict)
    user_queue.send(event)


def attention(event_dict):
    event_dict['Data'] = json.loads(event_dict['Data'])
    event = DyAttentionEvent(event_dict)
    user_queue.send(event)


async def dy_connect():
    session = aiohttp.ClientSession()
    async with session.ws_connect("ws://127.0.0.1:8888") as ws:
        await ws.send_str('token')
        async for message in ws:
            # print(f"Received message: {message}")
            # 处理websocket 消息
            if message.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(message.data)
                event_name = data.get("Type")  # 标签类型
                filter_map = {
                    1: msg,  # 1用户发言
                    2: ck,  # 2用户点赞
                    3: welcome,  # 3用户入房
                    4: attention,  # 用户关注
                    5: Gift,  # 5用户礼物
                    # 6: check,  # 6人数统计
                }
                if event_name in filter_map:
                    filter_map[event_name](data)

            elif msg.type == aiohttp.WSMsgType.CLOSED:
                break
            elif msg.type == aiohttp.WSMsgType.ERROR:
                break

    await ws.close()


if __name__ == '__main__':
    sync(dy_connect())
