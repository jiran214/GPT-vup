"""
 @Author: jiran
 @Email: jiran214@qq.com
 @FileName: monkey_patch.py
 @DateTime: 2023/5/13 12:53
 @SoftWare: PyCharm
 先导入这个文件，改写lib
"""
import configparser
import json
import os
import random
from contextlib import asynccontextmanager
from typing import AsyncIterator

import aiohttp
import urllib3
from aiohttp import TCPConnector
from openai import api_requestor
import openai

from src.modules.actions import plugin_info

urllib3.disable_warnings()


def initialize_openai():
    # 避免循环导入，多一次读取ini配置
    file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../config.ini')
    _config = configparser.RawConfigParser()
    _config.read(file_path)
    api_key = _config.get('openai', 'api_key')
    os.environ['OPENAI_API_KEY'] = api_key

    proxy = _config.get('other', 'proxy')
    if proxy:
        os.environ["http_proxy"] = f'http://{proxy}/'
        os.environ["https_proxy"] = f'http://{proxy}/'

    @asynccontextmanager
    async def aiohttp_session() -> AsyncIterator[aiohttp.ClientSession]:
        async with aiohttp.ClientSession(connector=TCPConnector(limit_per_host=5, ssl=False), trust_env=True) as session:
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
    await vts.connect()
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
    with open("./action.json", "w") as dump_f:
        json.dump(action_dict, dump_f)

    # 测试
    assert len(hotkey_list) == len(action_dict.keys())  # vts 和 本地的动作是否一致
    assert len(hotkey_list) not in (0, 1)  # 动作太少
    action = random.choice(hotkey_list)
    print('随机播放动作测试...', action)
    send_hotkey_request = vts.vts_request.requestTriggerHotKey(action)
    await vts.request(send_hotkey_request)
    await vts.close()