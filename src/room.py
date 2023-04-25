"""
 @Author: jiran
 @Email: jiran214@qq.com
 @FileName: room.py
 @DateTime: 2023/4/22 21:23
 @SoftWare: PyCharm
"""
from bilibili_api import live, sync

import config
from src.events import DanmuMsgEvent, SendGiftEvent, SuperChatMessageEvent, InteractWordEvent
from src.log import worker_logger

from src.utils import user_queue

room = live.LiveDanmaku(config.room_id)

logger = worker_logger


@room.on('DANMU_MSG')
async def on_danmaku_event_filter(event_dict):
    # # 收到弹幕
    # event = DanmuMsgEvent.filter(event_dict)
    event = DanmuMsgEvent(event_dict)
    user_queue.send(event)


@room.on('SUPER_CHAT_MESSAGE')
async def on_super_chat_message_event_filter(event_dict):
    # SUPER_CHAT_MESSAGE
    # info = event['data']['data']
    # user_info = info['user_info']
    # print('SUPER_CHAT_MESSAGE',
    #       user_info['uname'],
    #       user_info['face'],
    #
    #       info['message'],
    #       info['price'],
    #       info['start_time'],
    #       )
    event = SuperChatMessageEvent(event_dict)
    user_queue.send(event)


@room.on('SEND_GIFT')
async def on_gift_event_filter(event_dict):
    # 收到礼物
    # info = event_dict['data']['data']
    # print('SEND_GIFT',
    #       info['face'],
    #       info['uname'],
    #       info['action'],
    #       info['giftName'],
    #       info['timestamp'],
    #       )
    event = SendGiftEvent(event_dict)
    user_queue.send(event)


@room.on('INTERACT_WORD')
async def on_interact_word_event_filter(event_dict):
    # INTERACT_WORD
    # info = event_dict['data']['data']
    # fans_medal = info['fans_medal']
    # print('INTERACT_WORD',
    #       fans_medal['medal_name'],
    #       fans_medal['medal_level'],
    #       info['uname'],
    #       info['timestamp']
    #       )
    if not user_queue.event_queue.full():
        event = InteractWordEvent(event_dict)
        user_queue.send(event)

# @room.on('WELCOME')
# async def on_welcome_event_filter(event):
#     # 老爷进入房间
#     print(3, event)
#
#
# @room.on('WELCOME_GUARD')
# async def on_welcome_guard_event_filter(event):
#     # 房管进入房间
#     print(4, event)

if __name__ == '__main__':
    sync(room.connect())