import asyncio
import json
import random
import re
import time
from typing import Union

from langchain.chat_models import ChatOpenAI

from src import config
from src.config import keyword_str_list, live2D_actions, live2D_embeddings
from src.core.agent import get_knowledge_base_info
from src.db.vector_store import similarity_search_from_qdrant
from src.modules.audio import tts_save

from src.utils.dfa import DFA
from src.utils.enums import TxtMode, ActionMode
from src.utils.events import ScheduleEvent

from src.utils.exceptions import InterruptException, ParseException
from src.utils.init import initialize_corpus
from src.utils.log import vup_logger

from src.utils.prompt_temple import get_chat_prompt_template
from src.utils.utils import sync_get_embedding, get_openai_key, is_user_input, top_n_indices_from_embeddings, root
from src.utils.utils import Event

logger = vup_logger
sound_base_path = root('static/voice/{}.mp3')

chat = ChatOpenAI(temperature=config.temperature, max_retries=2, max_tokens=150,
                  openai_api_key="temp")


class Builder:
    forbidden_words_dfa = DFA(keyword_str_list)
    if config.corpus_plugin:
        corpus_map, corpus_dfa = initialize_corpus()

    def __init__(self, event: Event):
        self.event = event

        self.txt_embedding = None
        self.txt_mode: Union[TxtMode, None] = None
        self.action_mode: Union[ActionMode, None] = None

        self.corpus_match_list = None
        self.prompt_extra_kwargs = {
            "context": "",
            "action_react": "",
        }
        self.audio_txt = None
        self.action_name = None
        self.sound_path = None

        # 走chatGPT or 走本地知识库 or 走固定话术
        if is_user_input(self.event):
            # 默认
            self.txt_mode = TxtMode.GPT3dot5
            # corpus_plugin优先级最高
            if config.corpus_plugin and self.corpus_map:
                corpus_dfa: DFA = self.corpus_dfa
                dfa_match_list = corpus_dfa.match(self.event.prompt_kwargs['text'])
                if dfa_match_list:
                    corpus_words = [corpus_word['match'] for corpus_word in dfa_match_list]
                    logger.info(f'检索到语料关键词:{corpus_words}，准备检索语料库')
                    self.corpus_match_list = dfa_match_list
                    self.txt_mode = TxtMode.CORPUS
            elif config.knowledge_plugin:
                self.txt_mode = TxtMode.KNOWLEDGE_BASE
        else:
            self.txt_mode = TxtMode.DIRECTLY

        # 无动作 or 设定的动作 or embedding匹配 or gpt响应
        self.action_mode = self.event.action_mode

        # 如果全局action关闭，自动转换成None mode
        if (not config.action_plugin or not live2D_actions) and self.action_mode is not ActionMode.NONE:
            self.action_mode = ActionMode.NONE

    def build_txt_embedding(self):
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
        self.txt_embedding = sync_get_embedding([embedding_str])

    def build_prompt_extra_kwargs(self):
        prefix, suffix = "", ""
        human_template = self.event.human_template
        if self.txt_mode is TxtMode.KNOWLEDGE_BASE:
            # 额外参数
            content = get_knowledge_base_info(self.event.prompt_kwargs['text'])
            try:
                knowledge_base_info = json.loads(content)
            except ParseException as e:
                raise e
            collection_name = knowledge_base_info['工具名称']
            collection_input = knowledge_base_info['工具输入']
            docs = similarity_search_from_qdrant(query=collection_input, collection_name=collection_name, k=config.top_k)
            qdrant_context = [
                doc[0].page_content
                for doc in docs
            ]
            context = (
                "\n\n请你重复上下文的内容和口吻,做出对观众弹幕的回应，"
                f"你的回答里不能说你参考了上下文。参考内容上下文:{str(qdrant_context)}\n\n"
            )
            self.prompt_extra_kwargs['context'] = context
        if self.action_mode is ActionMode.FROM_GPT:
            action_react = (
                "\n\n你能根据你的回答内容做出以下行为的其中一个"
                f"\n{' '.join(live2D_actions)}"
                "\n在你的回答文本后面加上<行为>"
            )
            self.prompt_extra_kwargs['action_react'] = action_react

    def build_audio_txt(self):
        TxtFactory(self).build_audio_txt()

    def build_action(self):
        VTSActionFactory(self).build_action()

    def build_sound(self):
        # 使用 Edge TTS 生成回复消息的语音文件
        sound_path = sound_base_path.format(int(time.time()))
        asyncio.run(tts_save(self.audio_txt, sound_path))
        self.sound_path = sound_path

    def build(self):
        return self


class VTSActionFactory:

    def __init__(self, builder: Builder):
        self.builder = builder
        self.action_mode = builder.action_mode

    def build_action_from_user(self):
        action_name = self.builder.event.action_name
        self.builder.action_name = action_name

    def build_action_from_embedding(self):
        # 匹配动作
        action_name = live2D_actions[
            int(top_n_indices_from_embeddings(self.builder.txt_embedding, live2D_embeddings, top=1)[0])]
        self.builder.action_name = action_name

    def build_action_from_gpt(self):
        # 从gpt响应解析出动作
        pattern = '<(.*)>'
        match_str = re.search(pattern, self.builder.audio_txt)
        self.builder.audio_txt = self.builder.audio_txt.replace(match_str.group(0), '')
        action_name = match_str.group(1)
        self.builder.action_name = action_name

    def build_action_random(self):
        self.builder.action_name = random.choice(live2D_actions)

    def build_action(self):
        if self.action_mode is ActionMode.Embedding:
            self.build_action_from_embedding()

        elif self.action_mode is ActionMode.FROM_GPT and self.builder.txt_mode is not TxtMode.CORPUS:
            self.build_action_from_gpt()

        elif self.action_mode is ActionMode.FROM_GPT and self.builder.txt_mode is TxtMode.CORPUS:
            self.build_action_random()

        elif self.action_mode is ActionMode.NONE:
            # 如果为None，不会生成动作
            self.builder.action_name = None

        elif self.action_mode is ActionMode.FIXED_ACTION:
            self.build_action_from_user()


class TxtFactory:

    def __init__(self, builder: Builder):
        self.builder = builder
        self.txt_mode = builder.txt_mode

    def build_audio_txt_directly(self):
        self.builder.audio_txt = self.builder.event.get_audio_txt()

    def build_audio_txt_from_corpus(self):
        # 取match_list的第一个结果，查询第一个找到的语料
        match_word = self.builder.corpus_match_list[0]['match']
        # 根据match_word搜索语料
        for audio_txt, kw in self.builder.corpus_map.items():
            if match_word in kw:
                self.builder.audio_txt = audio_txt
                break
        if not self.builder.audio_txt:
            raise f'不应该不存在{self.builder.corpus_match_list}'

    def build_audio_txt_from_gpt(self):
        # 请求GPT
        messages = get_chat_prompt_template(self.builder.event.human_template). \
            format_messages(**self.builder.event.prompt_kwargs, **self.builder.prompt_extra_kwargs)
        chat.openai_api_key = get_openai_key()
        llm_res = chat.generate([messages])
        assistant_content = llm_res.generations[0][0].text
        # 违禁词判断
        if keyword_str_list:
            dfa_match_list = self.builder.forbidden_words_dfa.match(assistant_content)
            forbidden_words = [forbidden_word['match'] for forbidden_word in dfa_match_list]
            if dfa_match_list:
                msg = f'包含违禁词:{forbidden_words}，跳过本次语音生成'
                logger.warning(msg)
                raise InterruptException(msg)
        self.builder.audio_txt = self.builder.event.get_audio_txt(assistant_content)

    def build_audio_txt(self):
        if self.txt_mode is TxtMode.GPT3dot5:
            self.build_audio_txt_from_gpt()

        elif self.txt_mode is TxtMode.DIRECTLY:
            self.build_audio_txt_directly()

        elif self.txt_mode is TxtMode.KNOWLEDGE_BASE:
            self.build_audio_txt_from_gpt()

        elif self.txt_mode is TxtMode.CORPUS:
            self.build_audio_txt_from_corpus()

