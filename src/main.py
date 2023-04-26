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
    def send(task):
        ue = UserEvent(*task)
        ue.is_high_priority = True
        ue.action_index = live2D_actions.index('Anim Shake')
        user_queue.send(ue)

    def send_user_event_2_queue_short_time(tasks):
        if not user_queue.event_queue.full():
            send(random.choice(tasks))

    def send_user_event_2_queue_long_time(tasks):
        send(random.choice(tasks))

    time.sleep(30)
    # 清空任务
    schedule.clear()
    # 创建一个按3秒间隔执行任务
    schedule_tasks = [
        ('我想让你扮演说唱歌手。您将想出强大而有意义的歌词、节拍和节奏，让听众“惊叹”。你的歌词应该有一个有趣的含义和信息，'
         '人们也可以联系起来。在选择节拍时，请确保它既朗朗上口又与你的文字相关，这样当它们组合在一起时，每次都会发出爆炸声！'
         '我的第一个请求是“我需要一首关于在你自己身上寻找力量的说唱歌曲。”', '接下来我给大家表演一首说唱！{}'),

        ('我要你扮演诗人。你将创作出能唤起情感并具有触动人心的力量的诗歌。写任何主题或主题，'
         '但要确保您的文字以优美而有意义的方式传达您试图表达的感觉。您还可以想出一些短小的诗句，这些诗句仍然足够强大，可以在读者的脑海中留下印记。'
         '我的第一个请求是“我需要一首关于爱情的诗”。', '{}'),

        ('我希望你充当励志演说家。将能够激发行动的词语放在一起，让人们感到有能力做一些超出他们能力的事情。你可以谈论任何话题，但目的是确保你所说的话能引起听众的共鸣，激励他们努力实现自己的目标并争取更好的可能性。'
         '我的第一个请求是“我需要一个关于每个人如何永不放弃的演讲”。', '全体注意，我将发表一个演讲！{}'),

        ("我要你担任哲学老师。我会提供一些与哲学研究相关的话题，你的工作就是用通俗易懂的方式解释这些概念。"
         "这可能包括提供示例、提出问题或将复杂的想法分解成更容易理解的更小的部分。"
         "我的第一个请求是“我需要帮助来理解不同的哲学理论如何应用于日常生活。", '我想到一个深奥的道理，{}'),

        ("我想让你扮演讲故事的角色。您将想出引人入胜、富有想象力和吸引观众的有趣故事。它可以是童话故事、教育故事或任何其他类型的故事，"
         "有可能吸引人们的注意力和想象力。根据目标受众，您可以为讲故事环节选择特定的主题或主题，例如，如果是儿童，则可以谈论动物；如果是成年人，"
         "那么基于历史的故事可能会更好地吸引他们等等。请开始你的讲述？", '我给大家讲个故事吧{}')
    ]
    schedule.every(3).minutes.do(
        send_user_event_2_queue_short_time, schedule_tasks
    )
    schedule.every(9).minutes.do(
        send_user_event_2_queue_long_time, schedule_tasks
    )
    # schedule.run_all(delay_seconds=30)
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
        else:
            logger.debug(f'')

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