"""
 @Author: jiran
 @Email: jiran214@qq.com
 @FileName: opanAi.py
 @DateTime: 2023/4/7 15:21
 @SoftWare: PyCharm
 urllib3==1.25.11
 该文件已弃用
"""
import asyncio
import os

import time
from typing import AsyncIterator, List

import aiohttp
import openai
from openai import api_requestor

import requests.adapters
import urllib3

from src import config
from src.utils import GPT35Params
from src.log import request_logger

if config.proxy:
    os.environ["http_proxy"] = f'http://{config.proxy}/'
    os.environ["https_proxy"] = f'http://{config.proxy}/'
    # openai.proxy = f'http://{config.proxy}/'

openai.api_key = config.api_key

logger = request_logger
headers = {
    'Content-Type': 'application/json',
    'Authorization': f"Bearer {config.api_key}"
}

proxies = {
    'http': f'http://{config.proxy}/',
    'https': f'http://{config.proxy}/'
}


def make_session() -> requests.Session:
    s = requests.Session()
    s.verify = False
    s.proxies = proxies
    urllib3.disable_warnings()
    s.trust_env = True
    s.mount(
        "https://",
        requests.adapters.HTTPAdapter(max_retries=2),
    )
    return s


session = make_session()


# conn = aiohttp.TCPConnector(limit_per_host=5, ssl=False)



# 猴子补丁
if config.proxy:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # api_requestor._make_session = make_session
    setattr(api_requestor._thread_context, 'session', session)
    api_requestor.aiohttp_session = aiohttp_session


async def async_get_embedding(texts: List[str], model="text-embedding-ada-002"):
    res = await openai.Embedding.acreate(input=texts, model=model)
    if len(texts) == 1:
        return res['data'][0]['embedding']
    else:
        return [d['embedding'] for d in res['data']]


def sync_get_embedding(texts: List[str], model="text-embedding-ada-002"):
    res = openai.Embedding.create(input=texts, model=model)
    if len(texts) == 1:
        return res['data'][0]['embedding']
    else:
        return [d['embedding'] for d in res['data']]


async def async_chat(system_content, user_content):
    response = await openai.ChatCompletion.acreate(**GPT35Params(
        messages=[{'role': 'system', 'content': system_content}, {'role': 'user', 'content': user_content}],
        temperature=1,
        # max_tokens
    ).dict())
    return response['choices'][0]['message']['content']


def sync_chat(system_content, user_content):
    response = openai.ChatCompletion.create(**GPT35Params(
        messages=[{'role': 'system', 'content': system_content}, {'role': 'user', 'content': user_content}],
        temperature=1,
        # max_tokens
    ).dict())
    return response['choices'][0]['message']['content']




if __name__ == '__main__':
    for _ in range(2):
        t1 = time.time()
        # print(len(sync_chat('你是个AI主播', '该昵称已创建 进入直播间。请表示欢迎！并简短聊聊他加入的粉丝团苏北')))
        # print(len(await async_get_embedding(['该昵称已创建 进入直播间。请表示欢迎！并简短聊聊他加入的粉丝团苏北'])))
        # policy = asyncio.WindowsSelectorEventLoopPolicy()
        # asyncio.set_event_loop_policy(policy)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(async_chat('你是个AI主播', '该昵称已创建 进入直播间。请表示欢迎！并简短聊聊他加入的粉丝团苏北'))
        # print(time.time() - t1)
        # time.sleep(4)
