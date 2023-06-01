"""
 @Author: jiran
 @Email: jiran214@qq.com
 @FileName: main.py
 @DateTime: 2023/4/23 13:19
 @SoftWare: PyCharm
"""
import threading
import time
import schedule


from src import config
from src.utils.prompt_temple import get_schedule_task
from src.utils.events import UserEvent
from src.utils.utils import worker_logger
from src.rooms.bilibili import BlLiveRoom
from src.rooms.douyin import dy_connect

from src.utils.utils import user_queue, NewEventLoop
from src.core.vup import VtuBer

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


