"""
 @Author: jiran
 @Email: jiran214@qq.com
 @FileName: process.py
 @DateTime: 2023/4/22 22:17
 @SoftWare: PyCharm
"""
import asyncio
import threading
import time
from bilibili_api import sync

from src import config
from src.actions import live2D_actions, action_embeddings, play_action
from src.audio import tts_save, play_sound
from src.log import worker_logger
from src.base import Event
from src.opanAi import async_chat, sync_chat, async_get_embedding, top_n_indices_from_embeddings, sync_get_embedding
from src.utils import audio_lock, NewEventLoop

logger = worker_logger

base_path = './static/voice/{}.mp3'


class EventWorker:
    def __init__(self, event: Event):
        self.event = event
        self.sound_path = base_path.format(int(time.time()))

    async def generate_chat(self):
        # 请求GPT
        logger.debug(f"prompt:{self.event.prompt_kwargs['user_content']} 开始请求gpt")
        assistant_content = sync_chat(**self.event.prompt_kwargs)
        # assistant_content = await async_chat(**self.event.prompt_kwargs)
        t0 = time.time()
        # 使用 Edge TTS 生成回复消息的语音文件
        logger.debug(f"开始生成TTS 文件")
        await tts_save(self.event.get_audio_txt(assistant_content), self.sound_path)
        logger.debug(f"tts请求耗时:{time.time()-t0}")

    async def generate_action(self):
        # 是否手动设置
        if not self.event.action_index:
            logger.debug(f"开始生成动作")
            t0 = time.time()
            # 获取词向量
            # embedding = await async_get_embedding([self.event.prompt_kwargs['user_content']])
            embedding = sync_get_embedding([self.event.prompt_kwargs['user_content']])
            # 匹配动作
            self.event.action_index = top_n_indices_from_embeddings(embedding, action_embeddings, top=1)[0]
            logger.debug(f"动作请求耗时:{time.time()-t0}")

    async def output(self):
        logger.debug(f'path:{self.sound_path} 准备播放音频和动作')
        while audio_lock.locked():
            await asyncio.sleep(2)
        else:
            # 每句话间隔时间
            time.sleep(1)
        # 播放声音
        play_sound_thread = threading.Thread(target=play_sound, args=(self.sound_path,))
        play_sound_thread.start()
        # 播放动作
        await play_action(self.event.action_index)

        # play_sound_thread.join()
        # time.sleep(5)

    async def _run(self):
        await asyncio.gather(
            asyncio.create_task(self.generate_chat()),
            asyncio.create_task(self.generate_action()),
        )
        # await self.generate_chat()
        # await self.generate_action()
        await self.output()

    def run(self):
        t_loop = NewEventLoop()
        t_loop.run(self._run())


if __name__ == '__main__':
    logger.debug('123')
