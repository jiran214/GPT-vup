import os
import sys

path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, path)
sys.path.insert(1, os.path.dirname(path))

import fire
from src import config
from src.core.main import start_thread
from src.utils.init import initialize_action, initialize_openai
from src.utils.log import worker_logger
from src.utils.utils import NewEventLoop, get_openai_key
from src.utils.init import initialize_openai


initialize_openai()
logger = worker_logger


class Management:
    def __init__(self):
        try:
            assert config.api_key_list
        except:
            raise '请填写openai -> api_key！'

    def action(self):
        loop = NewEventLoop()
        loop.run(initialize_action())

    def run(self, name):
        tasks = []
        self.test_plugin_dependency()
        if name.lower() == 'douyin':
            tasks.append(start_thread('dy_producer'))
        elif name.lower() == 'bilibili':
            tasks.append(start_thread('bl_producer'))
        tasks.append(start_thread('user_producer'))
        tasks.append(start_thread('consumer'))
        for task in tasks:
            task.join()

    def test_net(self):
        from langchain import OpenAI
        import requests
        # 测试外网环境(可能异常)
        proxies = None
        if config.proxy:
            proxies = {
                'http': f'http://{config.proxy}/',
                'https': f'http://{config.proxy}/'
            }
        r = requests.get(url='https://www.youtube.com/', verify=False, proxies=proxies)
        assert r.status_code == 200
        # 测试openai库
        llm = OpenAI(temperature=config.temperature, openai_api_base=config.base_url, openai_api_key=get_openai_key(), verbose=config.debug)
        text = "python是世界上最好的语言 "
        print(llm(text))
        print('测试成功！')

    def test_plugin_dependency(self):
        if config.context_plugin:
            try:
                from pymilvus import connections, has_collection, Collection
                import cryptography
            except ImportError:
                raise 'Please run pip install pymilvus==2.0 cryptography parsel'

            try:
                connections.connect(
                    alias="default",
                    host=config.milvus['host'],
                    port=config.milvus['port']
                )
                assert has_collection(config.milvus['collection'])
                collection = Collection(config.milvus['collection'])
                assert collection.num_entities != 0
            except Exception as e:
                raise e

            logger.info('上下文插件已开启')
        if config.speech_plugin:
            try:
                from src.modules.speech_rec import speech_hotkey_listener
            except ImportError:
                raise 'Please run pip install pyaudio speech_recognition keyboard'
            logger.info('语音交互插件已开启')
        if config.action_plugin:
            try:
                import pyvts
            except ImportError:
                raise 'Please run pip install pyvts，then run python manager action'
            logger.info('动作响应插件已开启')
        if config.schedule_plugin:
            logger.info('循环任务插件已开启')


if __name__ == '__main__':
    """命令行启动，等同于下面的程序启动"""
    fire.Fire(Management)

    """测试"""
    # >> python manager.py test
    # Management().test_net()

    """启动程序"""
    # >> python manager.py run bilibili
    # Management().run('BiliBili')
    # Management().run('DouYin')

    """初始化"""
    # >> python manager.py action
    # Management().action()
