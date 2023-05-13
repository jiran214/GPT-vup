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
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings

from src import config
from src.config import live2D_actions, live2D_embeddings
from src.actions import play_action
from src.audio import tts_save, play_sound
from src.log import worker_logger
from src.base import Event
from src.utils import audio_lock, NewEventLoop, top_n_indices_from_embeddings

logger = worker_logger

base_path = './static/voice/{}.mp3'

chat = ChatOpenAI(temperature=0.9, max_retries=2, max_tokens=150)
embeddings = OpenAIEmbeddings()


class VtuBer:
    def __init__(self, event: Event):
        self.event = event
        self.sound_path = base_path.format(int(time.time()))

    async def generate_chat(self):
        # 请求GPT
        logger.debug(f"prompt:{self.event.prompt_messages[1]} 开始请求gpt")
        llm_res = chat.generate([self.event.prompt_messages])
        assistant_content = llm_res.generations[0][0].text
        # 使用 Edge TTS 生成回复消息的语音文件
        logger.debug(f"开始生成TTS 文件")
        t0 = time.time()
        await tts_save(self.event.get_audio_txt(assistant_content), self.sound_path)
        logger.debug(f"tts请求耗时:{time.time()-t0}")

    async def generate_action(self):
        if isinstance(self.event.action, str):
            # 是否手动设置
            logger.debug(f"开始生成动作")
            t0 = time.time()
            # 获取词向量
            embedding = embeddings.embed_query(self.event.action)
            # 匹配动作
            self.event.action = int(top_n_indices_from_embeddings(embedding, live2D_embeddings, top=1)[0])
            logger.debug(f"动作请求耗时:{time.time()-t0}")

    async def output(self):
        logger.debug(f'path:{self.sound_path} 准备播放音频和动作')
        while audio_lock.locked():
            await asyncio.sleep(1)
        else:
            # 每句话间隔时间
            time.sleep(0.5)
        # 播放声音
        play_sound_thread = threading.Thread(target=play_sound, args=(self.sound_path,))
        play_sound_thread.start()
        # 播放动作
        if config.action_plugin and isinstance(self.event.action, int):
            await play_action(self.event.action)
        # play_sound_thread.join()
        # time.sleep(5)

    async def _run(self):
        tasks = [asyncio.create_task(self.generate_chat())]
        if config.action_plugin and self.event.action:
            tasks.append(asyncio.create_task(self.generate_action()))
        await asyncio.gather(*tasks)
        await self.output()

    def run(self):
        t_loop = NewEventLoop()
        t_loop.run(self._run())


if __name__ == '__main__':
    logger.debug('123')
