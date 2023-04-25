"""
 @Author: jiran
 @Email: jiran214@qq.com
 @FileName: events.py
 @DateTime: 2023/4/23 16:05
 @SoftWare: PyCharm
"""
import time

from actions import live2D_actions
from base import Event

system_content = (
    "请扮演一个傲娇的AI虚拟主播，你的名字叫桃桃。不要回答任何敏感问题！"
    "不要强调你是主播，不准道歉，只需要回答问题！"
    "你是一个带有一定的高傲情绪，可能会在自我表现时表现出一些自大或骄傲的情绪，或者表现出一些自信或者不屑一顾的态度。"
    "有时会有一些任性或者固执的表现。在做出决定时可能会表现出一定的倔强和固执，"
    "可能不太容易妥协或者接受别人的意见。同时也有一定的可爱和迷人之处。"
    "她们可能会有一些俏皮或者撒娇的表现，或者在和自己关心的人相处时表现得特别温柔和可爱。"
)


class DanmuMsgEvent(Event):

    def get_kwargs(self):
        return {
            'content': self._event_dict['data']['info'][1],
            'user_name': self._event_dict['data']['info'][2][1],
            'time': self._event_dict['data']['info'][9]['ts']
        }

    @property
    def prompt_kwargs(self):
        return {
            'system_content': system_content,
            'user_content': self._kwargs['content']
        }

    def get_audio_txt(self, gpt_resp):
        return f"{self._kwargs['content']} {gpt_resp}"


class SuperChatMessageEvent(Event):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_high_priority = True

    def get_kwargs(self):
        info = self._event_dict['data']['data']
        user_info = info['user_info']
        return {
            'user_name': user_info['uname'],
            'face': user_info['face'],
            'message': info['message'],
            'price': info['price'],
            'time': info['start_time'],
        }

    @property
    def prompt_kwargs(self):
        return {
            'system_content': system_content,
            'user_content': self._kwargs['message']
        }

    def get_audio_txt(self, gpt_resp):
        return f"感谢{self._kwargs['user_name']}的sc。{self._kwargs['message']} {gpt_resp}"


class SendGiftEvent(Event):

    def get_kwargs(self):
        info = self._event_dict['data']['data']
        return {
            'user_name': info['uname'],
            'face': info['face'],
            'action': info['action'],
            'giftName': info['giftName'],
            'time': info['timestamp'],
            'content': f"{info['uname']}{info['action']}了{info['giftName']}。"
        }

    @property
    def prompt_kwargs(self):
        return {
            'system_content': system_content,
            'user_content': (
                "{content}"
                "请表示感谢，说一句赞美他的话！"
            ).format(
                content=self._kwargs['content']
            )
        }

    def get_audio_txt(self, gpt_resp):
        return f"{self._kwargs['content']}{gpt_resp}"


class InteractWordEvent(Event):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.action_index = live2D_actions.index('Shock Sign')

    def get_kwargs(self):
        info = self._event_dict['data']['data']
        fans_medal = info['fans_medal']
        return {
            'medal_name': fans_medal['medal_name'],
            'medal_level': fans_medal['medal_level'],
            'user_name': info['uname'],
            'content': f"{info['uname']} 进入直播间。",
            'time': info['timestamp']
        }

    @property
    def prompt_kwargs(self):
        return {
            'system_content': system_content,
            'user_content': (
                "{content}"
                "请表示欢迎！并简短聊聊他加入的粉丝团{medal_name}"
            ).format(
                content=self._kwargs['content'],
                medal_name=self._kwargs['medal_name']
            )
        }

    def get_audio_txt(self, gpt_resp):
        return f"{gpt_resp}"


class UserEvent(Event):

    def __init__(self, user_content, audio_txt_temple):
        super(UserEvent, self).__init__({'type': 'user_event'})

        self.user_content = user_content
        self.audio_txt_temple = audio_txt_temple

    def get_kwargs(self):
        return {
            'time': int(time.time())
        }

    @property
    def prompt_kwargs(self):
        return {
            'system_content': system_content,
            'user_content': (
                self.user_content
            )
        }

    def get_audio_txt(self, gpt_resp):
        return self.audio_txt_temple.format(gpt_resp)

# class EventsFactory:
#     worker_map = {
#         'DANMU_MSG': DanmuMsgEvent,
#         'SUPER_CHAT_MESSAGE': SuperChatMessageEvent,
#         'SEND_GIFT': SendGiftEvent,
#         'INTERACT_WORD': InteractWordEvent,
