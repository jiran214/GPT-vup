"""
 @Author: jiran
 @Email: jiran214@qq.com
 @FileName: base.py
 @DateTime: 2023/4/22 22:19
 @SoftWare: PyCharm
"""
from abc import abstractmethod
from functools import cached_property
from typing import Union

import time

from src import config
from src.utils.enums import TxtMode, ActionMode


class Event:
    def __init__(self, event_dict):
        self._event_dict = event_dict
        self.event_name = str(event_dict.get('type', '')) or str(event_dict.get('Type', ''))
        if not self.event_name:
            raise ValueError(f'不存在事件:{event_dict}')

        self._kwargs = self.get_kwargs()        # 是否优先处理
        self.is_high_priority = False

        self.action_mode = ActionMode(config.event_config_dict[self.event_name]['action']['mode'])
        self.action_name = config.event_config_dict[self.event_name]['action']['name']

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

    @abstractmethod
    def get_audio_txt(self, *args, **kwargs):
        """数字人说的话"""
        return None

    @property
    def time(self):
        """易读的时间"""
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self._kwargs['time']))

    @property
    def action(self) -> Union[None, str, int]:
        """
        :return:
            None: 该event不做任何动作
            str: zero-shot 匹配动作
        """
        return self._action_name

    def __repr__(self):
        return f'event-{self.event_name}-{self._kwargs}'
