"""
 @Author: jiran
 @Email: jiran214@qq.com
 @FileName: utils.py
 @DateTime: 2023/4/23 17:00
 @SoftWare: PyCharm
"""
import asyncio
import os.path
import queue
import random
import re
import time
from collections import deque

from threading import Lock
from dataclasses import dataclass

from typing import List, Union, Dict

import numpy as np
import openai
from cacheout import Cache
from decorator import decorator
from scipy import spatial

from src import config
from src.config import root_path
from src.utils.base import Event
from src.utils.events import BlSuperChatMessageEvent, BlDanmuMsgEvent, ScheduleEvent
from src.utils.log import worker_logger

logger = worker_logger
audio_lock = Lock()


def root(*args):
    return os.path.join(root_path, *args)


class NewEventLoop:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def run(self, coroutine):
        return self.loop.run_until_complete(coroutine)


@dataclass
class GPT35Params:
    messages: List  # 聊天格式的输入消息列表
    model: str = "gpt-3.5-turbo"  # 模型 ID，只支持 gpt-3.5-turbo 和 gpt-3.5-turbo-0301
    temperature: float = 1.5  # 采样温度，0~2 范围内的浮点数。较大的值会使输出更随机，较小的值会使输出更确定
    top_p: float = 1.0  # 替代采样温度的另一种方式，称为 nucleus 采样，只考虑概率质量排名前 top_p 的 token。范围在 0~1 之间
    n: int = 1  # 每个输入消息要生成的聊天完成选项数量，默认为 1
    stream: bool = False  # 是否启用流式输出
    stop: Union[str, List[str], None] = None  # 最多 4 个序列，当 API 生成的 token 包含任意一个序列时停止生成
    max_tokens: int = 1000  # 默认inf   # 生成的答案中允许的最大 token 数量，默认为 (4096 - prompt tokens)
    presence_penalty: float = None  # 0.0   # -2.0 到 2.0 之间的数字，用于基于新 token 是否出现在已有文本中惩罚模型。正数值会增加模型谈论新话题的可能性
    frequency_penalty: float = None  # 0.0   # -2.0 到 2.0 之间的数字，用于基于新 token 是否在已有文本中的频率惩罚模型。正数值会降低模型直接重复相同文本的可能性
    logit_bias: Dict[str, float] = None  # 一个将 token ID 映射到关联偏差值（-100 到 100）的 JSON 对象，用于修改指定 token 出现在完成中的可能性
    user: str = None  # 表示最终用户的唯一标识符，可帮助 OpenAI 监视和检测滥用

    def dict(self, exclude_defaults=False, exclude_none=True):
        res = {}
        for k, v in self.__dict__.items():
            if exclude_none:
                if v is None:
                    continue
            res[k] = v
        return res
        # dict(exclude_defaults=False, exclude_none=True)


class UserQueue:
    maxsize = 15

    def __init__(self):
        self.high_priority_event_queue = queue.Queue()
        self.event_queue = queue.Queue(self.maxsize)

    def send(self, event: Union[Event, None]):
        if not event:
            logger.debug(f'过滤:{event}')
            return
        # print(event._event_name)
        # Check if high-priority queue is full
        if event.is_high_priority:
            # Add object to high-priority queue
            self.high_priority_event_queue.put_nowait(event)
        else:
            # Check if main queue is full
            if not self.event_queue.full():
                # Add object to main queue
                self.event_queue.put_nowait(event)
            else:
                # Remove oldest item from queue and add new item
                self.event_queue.get()
                self.event_queue.put_nowait(event)

    def recv(self) -> Union[None, Event]:
        # Check high-priority queue first
        if not self.high_priority_event_queue.empty():
            # Remove oldest item from high-priority queue and process it
            event = self.high_priority_event_queue.get()
        elif not self.event_queue.empty():
            # Remove oldest item from main queue and process it
            event = self.event_queue.get()
        else:
            event = None
        return event

    def __str__(self):
        return f"event_queue 数量:{self.event_queue.qsize()} high_priority_event_queue 数量:{self.high_priority_event_queue.qsize()}"


user_queue = UserQueue()


class FixedLengthTSDeque:

    def __init__(self, per_minute_times):
        self._per_minute_times = per_minute_times
        self._data_deque = deque(maxlen=per_minute_times)

    def _append(self) -> None:
        self._data_deque.append(int(time.time()))

    def can_append(self):
        if len(self._data_deque) < self._per_minute_times or int(time.time()) - self._data_deque[0] > 60:
            return True
        return False

    def acquire(self):
        if not self.can_append():
            logger.warning('当前api_key调用频率超过3次/min,建议在config -> openai添加api_key')
            return False
        else:
            self._append()
            return True


def top_n_indices_from_embeddings(
        query_embedding: List[float],
        embeddings: List[List[float]],
        distance_metric="cosine",
        top=1
) -> list:
    """Return the distances between a query embedding and a list of embeddings."""
    distance_metrics = {
        "cosine": spatial.distance.cosine,
        "L1": spatial.distance.cityblock,
        "L2": spatial.distance.euclidean,
        "Linf": spatial.distance.chebyshev,
    }
    distances = [
        distance_metrics[distance_metric](query_embedding, embedding)
        for embedding in embeddings
    ]
    top_n_indices = np.argsort(distances)[:top]
    return top_n_indices


def sync_get_embedding(texts: List[str], model="text-embedding-ada-002"):
    res = openai.Embedding.create(input=texts, model=model, api_key=get_openai_key())
    if isinstance(texts, list) and len(texts) == 1:
        return res['data'][0]['embedding']
    else:
        return [d['embedding'] for d in res['data']]


api_key_limit_dict = dict(zip(config.api_key_list, [FixedLengthTSDeque(3) for _ in config.api_key_list]))
current_api_key = config.api_key_list[0]


def get_openai_key():
    global current_api_key
    times = 0
    while 1:
        times = times + 1
        if api_key_limit_dict[current_api_key].acquire():
            return current_api_key
        else:
            current_api_key = config.api_key_list[
                (config.api_key_list.index(current_api_key) + 1) % len(config.api_key_list)]
            # print('switch', current_api_key)
        if times > len(config.api_key_list):
            time.sleep(5)


def is_user_input(event: Event):
    return isinstance(event, BlDanmuMsgEvent) or isinstance(event, BlSuperChatMessageEvent)


def validate_string(input_string):
    pattern = r'^[\u4E00-\u9FA5A-Za-z\s]+$'
    # \u4E00-\u9FA5 是中文的 Unicode 范围，A-Za-z 是英文字母的范围，\s 匹配空格
    return bool(re.match(pattern, input_string))


@decorator
def time_record(func, record_logger, *args, **kw):
    record_logger.debug(f'func:{func.__name__}开始运行')
    t0 = time.time()
    func(*args, **kw)
    record_logger.debug(f"func:{func.__name__}运行成功-耗时:{time.time() - t0}")


cache = Cache()


class VupCache:
    def __init__(self, key):
        self.key = key

    @classmethod
    def can_cache(cls, event: Event):
        if is_user_input(event):
            text = event.prompt_kwargs.get('text')
            if len(text) <= 4:
                key = text
                return cls(key)
        return None

    def set_vup(self, value):
        cache.set(key=self.key, value=value)

    @staticmethod
    def get_vup(self):
        return cache.get(key=self.key)


if __name__ == '__main__':
    while 1:
        print(get_openai_key())
