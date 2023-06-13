"""
 @Author: jiran
 @Email: jiran214@qq.com
 @FileName: main.py
 @DateTime: 2023/4/23 13:19
 @SoftWare: PyCharm
"""
import os
import threading
import time
import schedule

from src import config
from src.core.builders import Builder
from src.utils.base import Event
from src.utils.exceptions import InterruptException
from src.utils.events import UserEvent, ScheduleEvent
from src.utils.utils import worker_logger, VupCache, root
from src.rooms.bilibili import BlLiveRoom
from src.rooms.douyin import dy_connect

from src.utils.utils import user_queue, NewEventLoop
from src.core.vup import Director, construct_from_schedule

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

    def send_high_priority_event_2_queue(self, event: Event):
        event.is_high_priority = True
        user_queue.send(event)

    def create_schedule(self):
        # 清空任务
        schedule.clear()
        # 延时启动
        # time.sleep(10)
        # 创建一个按5分钟间隔执行任务
        # schedule.every(5).minutes.do(
        #     self.send_user_event_2_queue, get_schedule_task()
        # )
        if config.schedule_event_dict:
            logger.info(f'发现schedule调度任务-数量:{len(config.schedule_event_dict)}-提前处理中,')
        else:
            logger.info('未发现定时任务')
        for event_name, event_dict in config.schedule_event_dict.items():
            event = construct_from_schedule(event_name, event_dict)
            logger.info(f'调度事件创建完毕:{event_name}')
            if frequency := event_dict.get('frequency'):
                schedule.every(float(frequency)).minutes.do(
                    self.send_high_priority_event_2_queue, event
                )
            elif timing := event_dict.get('timing'):
                schedule.every().day.at(timing).do(
                    self.send_high_priority_event_2_queue, event
                )
        return schedule

    def run(self):
        if config.schedule_plugin:
            schedule_obj = self.create_schedule()
            self.run_funcs.append(schedule_obj.run_pending)
        if config.speech_plugin:
            try:
                from src.modules.speech_rec import speech_hotkey_listener
            except ImportError:
                raise 'Please run pip install pyaudio speech_recognition keyboard'
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
        vup = None
        if not event:
            # Both queues are empty, wait for new items to be added
            time.sleep(1)
            logger.debug('consumer waiting')
            continue

        logger.debug(f'开始处理事件：{event}')
        if isinstance(event, ScheduleEvent):
            vup = event.vup
            vup.react()
            return

        elif cache := VupCache.can_cache(event):
            if vup := cache.get_vup():
                vup.react()
                logger.debug(f'缓存命中-{vup}')
                return

        builder = Builder(event)
        director = Director(builder)
        try:
            vup = director.construct()
            logger.debug(f'vup耗时:{time.time() - t0}')
        except InterruptException as e:
            logger.warning(e)
        except Exception as e:
            logger.exception(e)
            raise e

        if vup:
            vup.react()
            if cache := VupCache.can_cache(event):
                cache.set_vup(vup)


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
