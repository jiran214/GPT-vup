"""
 @Author: jiran
 @Email: jiran214@qq.com
 @FileName: process.py
 @DateTime: 2023/4/22 22:17
 @SoftWare: PyCharm
"""
import asyncio
import os
import threading
import time
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings

from src import config
from src.config import live2D_embeddings, keyword_str_list
from src.db.milvus import VectorStore
from src.db.models import TieBa
from src.db.mysql import get_session
from src.modules.actions import play_action
from src.modules.audio import tts_save, play_sound
from src.utils.dfa import DFA
from src.utils.events import BlDanmuMsgEvent
from src.utils.utils import worker_logger, sync_get_embedding, get_openai_key
from src.utils.utils import Event
from src.utils.utils import audio_lock, NewEventLoop, top_n_indices_from_embeddings

logger = worker_logger

base_path = './static/voice/{}.mp3'


class VtuBer:
    dfa = DFA(keyword_str_list)

    def __init__(self, event: Event):
        self.event = event
        self.sound_path = base_path.format(int(time.time()))

    async def generate_chat(self, embedding):
        # 额外参数
        extra_kwargs = {}
        # 只给弹幕增加上下文
        if config.context_plugin and isinstance(self.event, BlDanmuMsgEvent):
            ids = VectorStore(config.milvus['collection']).search_top_n_from_milvus(int(config.milvus['top_n']), embedding)[0].ids
            with get_session() as s:
                rows = s.query(TieBa).filter(TieBa.hash_id.in_(str(hash_id) for hash_id in ids)).all()
                context = [row.content for row in rows]
                extra_kwargs['context'] = str(context)
        # 请求GPT
        messages = self.event.get_prompt_messages(**extra_kwargs)
        logger.info(f"prompt:{messages[1]} 开始请求gpt")
        chat = ChatOpenAI(temperature=config.temperature, max_retries=2, max_tokens=150,
                          openai_api_key=get_openai_key())
        llm_res = chat.generate([messages])
        assistant_content = llm_res.generations[0][0].text
        logger.info(f'assistant_content:{assistant_content}')
        # 违禁词判断
        dfa_match_list = self.dfa.match(assistant_content)
        forbidden_words = [forbidden_word['match'] for forbidden_word in dfa_match_list]
        if dfa_match_list:
            logger.warning(f'包含违禁词:{forbidden_words}，跳过本次语音生成')
            return False
        # 使用 Edge TTS 生成回复消息的语音文件
        logger.debug(f"开始生成TTS 文件")
        t0 = time.time()
        await tts_save(self.event.get_audio_txt(assistant_content), self.sound_path)
        logger.debug(f"tts请求耗时:{time.time()-t0}")

    async def generate_action(self, embedding):
        if isinstance(self.event.action, str):
            # 是否手动设置
            logger.debug(f"开始生成动作")
            t0 = time.time()
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
        # 获取词向量
        str_tuple = ('text', 'content', 'message', 'user_name')
        prompt_kwargs = self.event.prompt_kwargs.copy()
        embedding_str = None
        for key in str_tuple:
            if key in prompt_kwargs:
                embedding_str = prompt_kwargs[key]
                break
        if not embedding_str:
            raise '不应该不存在'
        embedding = sync_get_embedding([embedding_str])
        tasks = [asyncio.create_task(self.generate_chat(embedding))]
        if config.action_plugin and self.event.action:
            tasks.append(asyncio.create_task(self.generate_action(embedding)))
        state = await asyncio.gather(*tasks)
        if state[0] is not False:
            await self.output()

    def run(self):
        t_loop = NewEventLoop()
        t_loop.run(self._run())


if __name__ == '__main__':

    res = embedding = sync_get_embedding(['embedding_str'])
    print(res)
    logger.debug('123')
