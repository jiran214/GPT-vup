"""
 @Author: jiran
 @Email: jiran214@qq.com
 @FileName: events.py
 @DateTime: 2023/4/23 16:05
 @SoftWare: PyCharm
"""
import time

from src.utils.utils import Event


class BlDanmuMsgEvent(Event):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.action = self._kwargs['content']

    def get_kwargs(self):
        return {
            'content': self._event_dict['data']['info'][1],
            'user_name': self._event_dict['data']['info'][2][1],
            'time': self._event_dict['data']['info'][9]['ts']
        }

    @property
    def prompt_kwargs(self):
        return {
            'text': self._kwargs['content']
        }

    @property
    def human_template(self):
        return '{text}'

    def get_audio_txt(self, gpt_resp):
        return f"{self._kwargs['content']} {gpt_resp}"


class BlSuperChatMessageEvent(Event):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_high_priority = True
        self.action = self._kwargs['message']

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
            'message': self._kwargs['message']
        }

    @property
    def human_template(self):
        return '{message}'

    def get_audio_txt(self, gpt_resp):
        return f"感谢{self._kwargs['user_name']}的sc。{self._kwargs['message']} {gpt_resp}"


class BlSendGiftEvent(Event):

    def get_kwargs(self):
        info = self._event_dict['data']['data']
        return {
            'user_name': info['uname'],
            'face': info['face'],
            'action': info['action'],
            'giftName': info['giftName'],
            'time': info['timestamp'],

        }

    @property
    def prompt_kwargs(self):
        return {
            'content': f"{self._kwargs['user_name']}{self._kwargs['action']}了{self._kwargs['giftName']}。"
        }

    @property
    def human_template(self):
        return (
            "{content}"
            "请表示感谢，说一句赞美他的话！"
        )

    def get_audio_txt(self, gpt_resp):
        return f"{self.prompt_kwargs['content']} {gpt_resp}"


class BlInteractWordEvent(Event):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
            'content': self._kwargs['content'],
            'medal_name': self._kwargs['medal_name']
        }

    @property
    def human_template(self):
        return (
            "{content}"
            "请表示欢迎！并简短聊聊他加入的粉丝团{medal_name}"
        )

    def get_audio_txt(self, gpt_resp):
        return f"{gpt_resp}"


class DyDanmuMsgEvent(BlDanmuMsgEvent):

    def get_kwargs(self):
        return {
            'content': self._event_dict['Data']['Content'],
            'user_name': self._event_dict['Data']['User']['Nickname'],
            'time': int(time.time())
        }


class DyCkEvent(Event):

    def get_kwargs(self):
        return {
            'user_name': self._event_dict['Data']['User']['Nickname'],
            'content': self._event_dict['Data']['Content'],
            'time': int(time.time())
        }

    @property
    def prompt_kwargs(self):
        return {
            'content': self._kwargs['user_name']
        }

    @property
    def human_template(self):
        return (
                "{content}给你点了赞，"
                "请表示感谢！"
        )

    def get_audio_txt(self, gpt_resp):
        return f"{gpt_resp}"


class DyWelcomeWordEvent(Event):

    def get_kwargs(self):
        return {
            'user_name': self._event_dict['Data']['User']['Nickname'],
            'time': int(time.time())
        }

    @property
    def prompt_kwargs(self):
        return {
            'user_name': self._kwargs['user_name']
        }

    @property
    def human_template(self):
        return (
            "{user_name}，进入直播间"
            "请表示欢迎！并简短聊聊他的名字"
        )

    def get_audio_txt(self, gpt_resp):
        return f"{gpt_resp}"


class DySendGiftEvent(Event):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_high_priority = True

    def get_kwargs(self):
        return {
            'user_name': self._event_dict['Data']['User']['Nickname'],
            'giftName': self._event_dict['Data']['GiftName'],
            'content': self._event_dict['Data']['Content'],
            'time': int(time.time())
        }

    @property
    def prompt_kwargs(self):
        return {
            'content': self._kwargs['content']
        }

    @property
    def human_template(self):
        return (
            "{content}"
            "请表示感谢，说一句赞美他的话！"
        )

    def get_audio_txt(self, gpt_resp):
        return f"{self._kwargs['user_name']} 送出{self._kwargs['giftName']}!{gpt_resp}"


class DyAttentionEvent(Event):

    def get_kwargs(self):
        return {
            'user_name': self._event_dict['data']['User']['Nickname'],
            'content': self._event_dict['data']['Content'],
            'time': int(time.time())
        }

    @property
    def prompt_kwargs(self):
        return {
            'user_name': self._kwargs['user_name']
        }

    @property
    def human_template(self):
        return (
            "{user_name}关注了你！"
            "请表示感谢，说一句赞美他的话！"
        )

    def get_audio_txt(self, gpt_resp):
        return gpt_resp


class UserEvent(Event):

    def __init__(self, content, audio_txt_temple):
        super(UserEvent, self).__init__({'type': 'user_event'})
        self.content = content
        self.audio_txt_temple = audio_txt_temple

    def get_kwargs(self):
        return {
            'time': int(time.time())
        }

    @property
    def prompt_kwargs(self):
        return {
            'content': self.content
        }

    @property
    def human_template(self):
        return '{content}'

    def get_audio_txt(self, gpt_resp):
        return self.audio_txt_temple.format(gpt_resp)

