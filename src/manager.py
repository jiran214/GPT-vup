from src import config
from src.core.main import start_thread
from src.db.dao import engine, Base
from src.utils.init import initialize_action, update_knowledge, import_corpus
from src.utils.log import worker_logger
from src.utils.utils import NewEventLoop, get_openai_key

logger = worker_logger


try:
    assert config.api_key_list
except:
    raise '请填写openai -> api_key！'


def action():
    loop = NewEventLoop()
    loop.run(initialize_action())


def knowledge():
    update_knowledge()


def corpus():
    Base.metadata.create_all(engine)
    import_corpus()


def run(name):
    test_plugin_dependency()
    if name.lower() == 'douyin':
        start_thread('dy_producer')
    elif name.lower() == 'bilibili':
        start_thread('bl_producer')
    start_thread('user_producer')
    start_thread('consumer')


def test_net():
    from langchain import OpenAI
    import requests
    # 测试外网环境(可能异常)
    r = requests.get(url='https://www.youtube.com/', verify=False, proxies={
        'http': f'http://{config.proxy}/',
        'https': f'http://{config.proxy}/'
    })
    assert r.status_code == 200
    # 测试openai库
    llm = OpenAI(temperature=config.temperature, openai_api_key=get_openai_key(), verbose=config.debug)
    text = "python是世界上最好的语言 "
    print(llm(text))
    print('测试成功！')


def test_plugin_dependency():
    if config.knowledge_plugin:
        try:
            import qdrant_client, cryptography, tiktoken, pypdf
        except ImportError:
            raise 'Please run pip install qdrant tiktoken pypdf. ps:安装过程中可能会遇到各种依赖问题'
        logger.info('知识库插件已开启')
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

    if config.corpus_plugin:
        logger.info('插件已开启')


if __name__ == '__main__':
    """命令行启动，等同于下面的程序启动"""
    # fire.Fire()

    """测试"""
    # >> python manager.py test
    # test_net()

    """启动程序"""
    # >> python manager.py run bilibili
    run('BiliBili')
    # run('DouYin')

    """初始化动作"""
    # >> python manager.py action
    # action()

    """初始化语料库"""
    # >> python manager.py corpus
    # corpus()
