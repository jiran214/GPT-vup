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
import schedule

from src.actions import live2D_actions
from src.events import UserEvent
from src.log import worker_logger
from src.room import room
from src.utils import user_queue, NewEventLoop
from src.workers import EventWorker

logger = worker_logger


# Define the producer function
def producer():
    t_loop = NewEventLoop()
    t_loop.run(room.connect())


def user_producer():
    def send_user_event_2_queue(user_content, audio_txt_temple):
        ue = UserEvent(user_content, audio_txt_temple)
        ue.is_high_priority = True
        ue.action_index = live2D_actions.index('Anim Shake')
        user_queue.send(ue)

    # 清空任务
    schedule.clear()
    # 创建一个按3秒间隔执行任务
    schedule.every(8).minutes.do(
        send_user_event_2_queue,
        '请讲一个冷笑话',
        '我给大家讲一个冷笑话吧~{}'
    )
    # 创建一个按3秒间隔执行任务
    schedule.every(6).minutes.do(
        send_user_event_2_queue,
        '请表演一个节目',
        '我给大家讲一个冷笑话吧~{}'
    )
    # 创建一个按2秒间隔执行任务
    schedule.every(4).minutes.do(
        send_user_event_2_queue,
        '请给观众老爷做一个自我介绍',
        '我给做个自我介绍吧~{}'
    )
    schedule.run_all(delay_seconds=30)
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
            continue

        worker = EventWorker(event)
        try:
            worker.run()
            logger.debug(f'worker耗时:{time.time() - t0}')
        except Exception as e:
            # raise e
            logger.error(e)
        # time.sleep(20)


if __name__ == '__main__':
    # 初始化live2d 动作和向量
    # sync(initialize_action())

    # 创建生产者线程
    producer_thread = threading.Thread(target=producer)
    producer_thread.start()
    logger.debug('producer 启动...')

    producer_thread = threading.Thread(target=user_producer)
    producer_thread.start()
    logger.debug('user_producer 启动...')

    # 创建消费者线程
    consumer_thread = threading.Thread(target=consumer)
    consumer_thread.start()
    logger.debug('consumer 启动...')