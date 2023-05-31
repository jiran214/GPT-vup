"""
 @Author: jiran
 @Email: jiran214@qq.com
 @FileName: main.py
 @DateTime: 2023/4/23 13:19
 @SoftWare: PyCharm
"""

import os

import sys

path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, path)
sys.path.insert(1, os.path.dirname(path))

import threading
import time
import schedule

import fire

import config
from src.utils.utils import get_schedule_task
from langchain import OpenAI
from src.modules.speech_rec import speech_hotkey_listener
from src.utils.utils import UserEvent
from src.utils.utils import worker_logger
from src.rooms.bilibili import BlLiveRoom
from src.rooms.douyin import dy_connect

from src.utils.utils import user_queue, NewEventLoop
from src.workers import VtuBer
from src.utils.init import initialize_openai, initialize_action

logger = worker_logger


# Define the producer function
def bl_producer():
    r = BlLiveRoom()
    t_loop = NewEventLoop()
    t_loop.run(r.connect())


def dy_producer():
    t_loop = NewEventLoop()
    t_loop.run(dy_connect())


class UserProducer:

    def __init__(self):
        self.run_funcs = []

    def send_user_event_2_queue(self, task):
        if user_queue.event_queue.empty():
            ue = UserEvent(*task)
            ue.is_high_priority = True
            # ue.action = live2D_actions.index('Anim Shake')
            user_queue.send(ue)

    def create_schedule(self):
        # 延时启动
        time.sleep(30)
        # 清空任务
        schedule.clear()
        # 创建一个按5分钟间隔执行任务
        schedule.every(5).minutes.do(
            self.send_user_event_2_queue, get_schedule_task()
        )
        return schedule

    def run(self):
        if config.schedule_plugin:
            schedule_obj = self.create_schedule()
            self.run_funcs.append(schedule_obj.run_pending)
        if config.speech_plugin:
            # self.run_funcs.append(speech_hotkey_listener)
            speech_hotkey_listener()
        if self.run_funcs:
            self.run_funcs.append(lambda: time.sleep(2))
            while True:
                for run_fun in self.run_funcs:
                    run_fun()


# Define the consumer function
def consumer():
    while True:
        t0 = time.time()
        event = user_queue.recv()
        if not event:
            # Both queues are empty, wait for new items to be added
            time.sleep(1)
            logger.debug('consumer waiting')
            continue

        worker = VtuBer(event)
        try:
            worker.run()
            logger.debug(f'worker耗时:{time.time() - t0}')
        except Exception as e:
            raise e
            # logger.error(e)
        # time.sleep(20)


def start_thread(worker_name):
    worker_map = {
        'bl_producer': bl_producer,
        'dy_producer': dy_producer,
        'user_producer': UserProducer().run,
        'consumer': consumer
    }
    if worker_name not in worker_map:
        raise '不存在...'

    thread = threading.Thread(target=worker_map[worker_name])
    thread.start()


class Management:

    def __init__(self):
        initialize_openai()

    def action(self):
        loop = NewEventLoop()
        loop.run(initialize_action())

    def run(self, name):
        if name.lower() == 'douyin':
            start_thread('dy_producer')
        elif name.lower() == 'bilibili':
            start_thread('bl_producer')
        start_thread('user_producer')
        start_thread('consumer')

    def test(self):
        # 检查库是否安装完全
        try:
            import openai, langchain, aiohttp, requests, bilibili_api
        except Exception as e:
            raise e
        # 测试外网环境(可能异常)
        r = requests.get(url='https://www.youtube.com/', verify=False, proxies={
            'http': f'http://{config.proxy}/',
            'https': f'http://{config.proxy}/'
        })
        assert r.status_code == 200
        # 测试openai库
        llm = OpenAI(temperature=0.9)
        text = "跟我说 python是世界上最好的语言 "
        print(llm(text))
        print('测试成功！')


if __name__ == '__main__':
    """命令行启动，等同于下面的程序启动"""
    fire.Fire(Management)

    """测试"""
    # >> python main test
    # Management().test()

    """启动程序"""
    # >> python main run bilibili
    # Management().run('BiliBili')
    # Management().run('DouYin')

    """初始化"""
    # >> python main action
    # Management().action()
