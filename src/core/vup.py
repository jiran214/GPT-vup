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

from src import config
from src.core.builders import Builder
from src.modules.actions import play_action
from src.modules.audio import tts_save, play_sound
from src.utils.enums import TxtMode, ActionMode
from src.utils.events import ScheduleEvent
from src.utils.log import vup_logger
from src.utils.utils import audio_lock, NewEventLoop, top_n_indices_from_embeddings, root

logger = vup_logger

sound_base_path = root('static/voice/{}.mp3')


def construct_from_schedule(event_name, schedule_dict):
    """
    提前生产音频和动作并做缓存，构造直接取出结果
    Returns:

    """
    audio_txt = schedule_dict['audio_txt']
    action_mode = ActionMode.FIXED_ACTION

    action_name = schedule_dict['action']['name']
    sound_path = sound_base_path.format(event_name)
    if not os.path.exists(sound_path):
        asyncio.run(tts_save(audio_txt, sound_path))
    vup = VtuBerV2(sound_path, audio_txt, action_name)
    return ScheduleEvent(vup)


class Director:
    def __init__(self, builder: Builder):
        self.builder = builder

        self.txt_mode: TxtMode = builder.txt_mode
        self.action_mode: ActionMode = builder.action_mode

    """
        build_txt_embedding 生成embedding
        build_prompt 构建prompt，某些条件下包含知识库的上下文
        
        build_audio_txt_from_gpt 从gpt获取文本
        build_audio_txt_from_corpus 从语料库获取文本
        
        build_action_from_user 从用户配置获取动作
        build_action_from_gpt 从gpt解析获取动作
        build_action_from_embedding 从embedding获取动作
        
        build_sound 生成语音
        build
    txt_mode、action_mode、config决定建造过程
    """

    async def async_construct(self):
        # 1. 获取向量
        if self.txt_mode is TxtMode.KNOWLEDGE_BASE or self.action_mode is ActionMode.Embedding:
            logger.debug('向量开始获取')
            t0 = time.time()
            self.builder.build_txt_embedding()
            logger.debug(f"向量获取成功-耗时:{time.time() - t0}")

        # 2. 获取文本
        logger.debug('文本开始获取')
        t0 = time.time()
        if self.txt_mode is TxtMode.GPT3dot5 and self.txt_mode is TxtMode.KNOWLEDGE_BASE:
            self.builder.build_prompt_extra_kwargs()
        self.builder.build_audio_txt()
        logger.debug(f"文本获取成功-耗时:{time.time() - t0}-txt_mode:{self.txt_mode}-prompt:{self.builder.messages}-audio_txt:{self.builder.audio_txt}")

        # 3. 获取动作
        logger.debug('文本开始获取')
        t0 = time.time()
        t = None
        if self.action_mode is not ActionMode.FROM_GPT:
            t = threading.Thread(target=self.builder.build_action)
            t.start()
        else:
            self.builder.build_action()
        logger.debug(f"文本获取成功-耗时:{time.time() - t0}-action_mode:{self.builder.action_name}-action_name:{self.builder.action_name}")

        # 4. 生成语音
        logger.debug('语音开始生成')
        t0 = time.time()
        await self.builder.build_sound()
        logger.debug(f"语音开始生成-耗时:{time.time() - t0}")

        if t:
            t.join()

        return VtuBerV2(
            sound_path=self.builder.sound_path,
            audio_txt=self.builder.audio_txt,
            action_name=self.builder.action_name
        )

    def sync_construct(self):
        ...

    def construct(self):
        t_loop = NewEventLoop()
        vup = t_loop.run(self.async_construct())
        return vup


class VtuBerV2:

    def __init__(self, sound_path, audio_txt, action_name):
        self.sound_path = sound_path
        self.audio_txt = audio_txt
        self.action_name = action_name

    def _speak(self):
        # 播放声音
        play_sound_thread = threading.Thread(target=play_sound, args=(self.sound_path,))
        play_sound_thread.start()

    async def _action(self):
        # 播放动作
        if config.action_plugin and isinstance(self.action_name, str):
            await play_action(self.action_name)

    async def _react(self):
        logger.info(f'Vup 成功获取Event响应-音频:{self.audio_txt}-动作:{self.action_name}')
        while audio_lock.locked():
            await asyncio.sleep(1)
        else:
            # 每句话间隔时间
            time.sleep(0.5)
        self._speak()
        # 动作延迟时间
        time.sleep(1)
        await self._action()

    def react(self):
        t_loop = NewEventLoop()
        t_loop.run(self._react())

    def __str__(self):
        return f'vup-audio_txt:{self.audio_txt}-action_name:{self.action_name}'


if __name__ == '__main__':
    # res = embedding = sync_get_embedding(['embedding_str'])
    pass
    # print(res)
    # logger.debug('123')
