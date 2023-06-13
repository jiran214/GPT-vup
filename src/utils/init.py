"""
 @Author: jiran
 @Email: jiran214@qq.com
 @FileName: monkey_patch.py
 @DateTime: 2023/5/13 12:53
 @SoftWare: PyCharm
 先导入这个文件，改写lib
"""
import asyncio
import configparser
import json
import os
import random
import time
from typing import List, Set, Dict

from contextlib import asynccontextmanager
from typing import AsyncIterator

import json
import os
import shutil
import aiohttp
import urllib3
from aiohttp import TCPConnector
from openai import api_requestor
import openai
import re

from src.config import root_path
from src.modules.actions import plugin_info
from src.db.dao import get_session
from src.db.models import Corpus
from src.utils.dfa import DFA
from src.scripts.vector_process import save_2_qdrant, Loader
from src.config import root, cfg
from src.utils.log import worker_logger
from src.utils.utils import validate_string

urllib3.disable_warnings()


def initialize_openai():
    # 避免循环导入，多一次读取ini配置
    file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../config.ini')
    _config = configparser.RawConfigParser()
    _config.read(file_path)
    proxy = _config.get('other', 'proxy')
    if proxy:
        os.environ["http_proxy"] = f'http://{proxy}/'
        os.environ["https_proxy"] = f'http://{proxy}/'

    @asynccontextmanager
    async def aiohttp_session() -> AsyncIterator[aiohttp.ClientSession]:
        async with aiohttp.ClientSession(connector=TCPConnector(limit_per_host=5, ssl=False),
                                         trust_env=True) as session:
            # async with aiohttp.ClientSession(trust_env=True) as session:
            yield session

    api_requestor.aiohttp_session = aiohttp_session


async def initialize_action():
    # websocket连接 获取token到本地
    try:
        import pyvts
    except ImportError:
        raise 'Please run pip install pyvts'
    vts = pyvts.vts(plugin_info=plugin_info)
    try:
        await vts.connect()
    except ConnectionRefusedError:
        raise '请先打开VTS，并打开API开关！'
    print('请在live2D VTS弹窗中点击确认！')
    await vts.request_authenticate_token()  # get token
    await vts.write_token()
    await vts.request_authenticate()  # use token

    response_data = await vts.request(vts.vts_request.requestHotKeyList())
    hotkey_list = []
    for hotkey in response_data['data']['availableHotkeys']:
        hotkey_list.append(hotkey['name'])
    print('读取到所有模型动作:', hotkey_list)

    # 请求embedding
    print('请求embedding模型中...')
    try:
        initialize_openai()
        res = await openai.Embedding.acreate(input=hotkey_list, model="text-embedding-ada-002")
        action_embeddings = [d['embedding'] for d in res['data']]
        action_dict = dict(zip(hotkey_list, action_embeddings))
        print(len(action_dict))
    except Exception as e:
        print('很可能是翻墙有问题')
        raise e

    # 写入
    with open(cfg("action.json"), "w") as dump_f:
        json.dump(action_dict, dump_f)

    # 测试
    assert len(hotkey_list) == len(action_dict.keys())  # vts 和 本地的动作是否一致
    assert len(hotkey_list) not in (0, 1)  # 动作太少
    action = random.choice(hotkey_list)
    print('随机播放动作测试...', action)
    send_hotkey_request = vts.vts_request.requestTriggerHotKey(action)
    await vts.request(send_hotkey_request)
    await vts.close()


def initialize_corpus() -> (List[Dict[str, Set[str]]], DFA):
    try:
        corpus_map = []
        keyword_list = []
        with get_session() as s:
            data_list = s.query(Corpus).all()
            for row in data_list:
                keywords = row.keywords.split(' ')
                keyword_list.extend(keywords)
                corpus_map.append({row.audio_txt: set(keywords)})
        corpus_dfa = DFA(keyword_list)
        return corpus_map, corpus_dfa
    except Exception as e:
        worker_logger.exception('corpus加载到内存错误', e)
        raise e


target_dir = root("static/documents")
logger = worker_logger


def update_knowledge(folder_path=target_dir):
    with open(cfg("knowledge.json"), 'r', encoding='utf-8') as f:
        knowledge_cfg_dict = json.load(f)
    for file_name in os.listdir(folder_path):
        if file_name in ('.gitkeep', None):
            continue
        if file_name in knowledge_cfg_dict:
            logger.info(f'{file_name}文件已存入向量数据库，无需更新')
            continue

        logger.info(f'正在处理{file_name}文件...')
        loader = Loader(file_name)
        docs = loader.load()
        collection_name = file_name.split('.')[:-1]
        save_2_qdrant(collection_name=collection_name, docs=docs)

        knowledge_cfg = {
            "file_name": file_name,
            "desc": "",
            "source": file_name,
            "switch": True
        }

        knowledge_cfg_dict[collection_name] = knowledge_cfg
        with open(cfg("knowledge.json"), 'w', encoding='utf-8') as f:
            json.dump(knowledge_cfg_dict, f, ensure_ascii=False)
        logger.info(f'docs成功存入qdrant-数量:{len(docs)}-collection_name{collection_name}')

    logger.info("over")


def __delete():
    # 遍历目录下的所有文件并删除
    for filename in os.listdir(target_dir):
        file_path = os.path.join(target_dir, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"删除文件 {file_path} 失败：{e}")
    print("over")


def import_corpus():
    with open(os.path.join(root_path, 'corpus.json'), mode='r', encoding='utf-8') as load_f:
        data_list = json.load(load_f)

    with get_session() as s:
        for data_dict in data_list:
            if not validate_string(data_dict['keywords']):
                raise ValueError(f"keywords错误,{data_dict['keywords']}")
            s.add(Corpus(**data_dict))



