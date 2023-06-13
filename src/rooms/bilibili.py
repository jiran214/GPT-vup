"""
 @Author: jiran
 @Email: jiran214@qq.com
 @FileName: room.py
 @DateTime: 2023/4/22 21:23
 @SoftWare: PyCharm
"""
from bilibili_api import sync

from src import config
from src.utils.events import BlDanmuMsgEvent, BlSendGiftEvent, BlSuperChatMessageEvent, BlInteractWordEvent
from src.utils.utils import worker_logger

from src.utils.utils import user_queue


logger = worker_logger


class BlLiveRoom:
    def __init__(self, bl_room_id=config.room_id):
        try:
            from bilibili_api import live, sync
        except ImportError:
            raise 'Please run pip install bilibili-api-python'
        self.room = live.LiveDanmaku(bl_room_id)
        self.add_event_listeners()

    def add_event_listeners(self):
        listener_map = {
            'DANMU_MSG': on_danmaku_event_filter,
            'SUPER_CHAT_MESSAGE': on_super_chat_message_event_filter,
            'SEND_GIFT': on_gift_event_filter,
            'INTERACT_WORD': on_interact_word_event_filter,
        }
        # 取消用户不需要的事件监听
        for event_name in config.bili_room_event_config_dict:
            listener_map.pop(event_name)
        for item in listener_map.items():
            self.room.add_event_listener(*item)

    def connect(self):
        return self.room.connect()


async def on_danmaku_event_filter(event_dict):
    # # 收到弹幕
    # event = BlDanmuMsgEvent.filter(event_dict)
    event = BlDanmuMsgEvent(event_dict)
    user_queue.send(event)


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
    event = BlSuperChatMessageEvent(event_dict)
    user_queue.send(event)


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
    event = BlSendGiftEvent(event_dict)
    user_queue.send(event)


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
        event = BlInteractWordEvent(event_dict)
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
    r = BlLiveRoom()
    sync(r.connect())