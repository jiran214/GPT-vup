"""
 @Author: jiran
 @Email: jiran214@qq.com
 @FileName: base.py
 @DateTime: 2023/4/22 22:19
 @SoftWare: PyCharm
"""
from abc import abstractmethod

import time

from prompt_temple import get_chat_prompt_template


class Event:
    def __init__(self, event_dict):
        self._event_dict = event_dict
        self._event_name = event_dict.get('type', '') or event_dict.get('Type', '')
        if not self._event_name:
            raise

        self._kwargs = self.get_kwargs()
        # 是否优先处理
        self.is_high_priority = False
        # 给这个event的动作
        self.action_index = None

    @abstractmethod
    def get_kwargs(self):
        """初始化event中有用的数据"""
        return {
            'time': None
        }

    @property
    @abstractmethod
    def prompt_kwargs(self):
        """提示模板需要用到的数据"""
        return {
            'time': None
        }

    @property
    @abstractmethod
    def human_template(self):
        """每类event对应的模板"""
        return '{text}'

    @property
    def prompt_messages(self):
        """出口函数，生成prompt，给到llm调用"""
        return get_chat_prompt_template(self.human_template).format_prompt(**self.prompt_kwargs)

    @abstractmethod
    def get_audio_txt(self, *args, **kwargs):
        """数字人说的话"""
        return None

    @property
    def time(self):
        """易读的时间"""
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self._kwargs['time']))
