"""
 @Author: jiran
 @Email: jiran214@qq.com
 @FileName: main.py
 @DateTime: 2023/4/23 13:19
 @SoftWare: PyCharm
"""
# Create a high-priority queue with a maximum size of 5
import threading

import time
import random
import schedule

from prompt_temple import get_schedule_task
from src.actions import live2D_actions
from src.events import UserEvent
from src.log import worker_logger
from src.rooms.bilibili import BlLiveRoom
from src.rooms.douyin import dy_connect

from src.utils import user_queue, NewEventLoop
from src.workers import EventWorker

logger = worker_logger


# Define the producer function
def bl_producer():
    r = BlLiveRoom()
    t_loop = NewEventLoop()
    t_loop.run(r.connect())


def dy_producer():
    t_loop = NewEventLoop()
    t_loop.run(dy_connect())


def user_producer():
    def send_user_event_2_queue():
        if user_queue.event_queue.empty():
            ue = UserEvent(get_schedule_task())
            ue.is_high_priority = True
            ue.action_index = live2D_actions.index('Anim Shake')
            user_queue.send(ue)
    # 延时启动
    time.sleep(30)
    # 清空任务
    schedule.clear()
    # 创建一个按5分钟间隔执行任务
    schedule.every(5).minutes.do(
        send_user_event_2_queue
    )
    while True:
        schedule.run_pending()
        time.sleep(10)


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

        worker = EventWorker(event)
        try:
            worker.run()
            logger.debug(f'worker耗时:{time.time() - t0}')
        except Exception as e:
            # raise e
            logger.error(e)
        # time.sleep(20)


def start_thread(worker_name):
    worker_map = {
        'bl_producer': bl_producer,
        'dy_producer': dy_producer,
        'user_producer': user_producer,
        'consumer': consumer
    }
    if worker_name not in worker_map:
        raise '不存在...'

    thread = threading.Thread(target=worker_map[worker_name])
    thread.start()


class Master:

    def __init__(self, name):
        self.name = name

    def run(self):
        if self.name == 'DouYin':
            start_thread('dy_producer')
        elif self.name == 'BiliBili':
            start_thread('bl_producer')
        start_thread('user_producer')
        start_thread('consumer')


if __name__ == '__main__':
    # Master('DouYin').run()
    Master('BiliBili').run()