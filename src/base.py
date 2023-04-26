"""
 @Author: jiran
 @Email: jiran214@qq.com
 @FileName: base.py
 @DateTime: 2023/4/22 22:19
 @SoftWare: PyCharm
"""
from abc import abstractmethod

import time


class Event:
    def __init__(self, event_dict):
        self._event_dict = event_dict
        self._event_name = event_dict.get('type', '') or event_dict.get('Type', '')
        if not self._event_name:
            raise

        self._kwargs = self.get_kwargs()

        self.is_high_priority = False
        self.action_index = None

    @abstractmethod
    def get_kwargs(self):
        return {
            'time': None
        }

    @property
    @abstractmethod
    def prompt_kwargs(self):
        ...
        return None

    @abstractmethod
    def get_audio_txt(self, *args, **kwargs):
        ...
        return None

    @property
    def time(self):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self._kwargs['time']))
