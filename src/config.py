"""
 @Author: jiran
 @Email: jiran214@qq.com
 @FileName: config.py
 @DateTime: 2023/4/7 14:30
 @SoftWare: PyCharm
"""
import configparser
import json
import os.path


def root(*args):
    return os.path.join(root_path, *args)


def static(*args):
    return os.path.join(root_path, 'static', *args)


def cfg(arg):
    return os.path.join(root_path, 'more_configs', arg)


root_path = os.path.abspath(os.path.dirname(__file__))
file_path = os.path.join(root_path, 'config.ini')

_config = configparser.RawConfigParser()
_config.read(file_path)

tss_settings = dict(_config.items('edge-tss'))

api_key_list = [value for key, value in _config.items('openai') if key.startswith('api') and value]
temperature = _config.get('openai', 'temperature')
room_id = _config.getint('room', 'id')
mysql = dict(_config.items('mysql'))
sqlite = dict(_config.items('sqlite'))
# milvus = dict(_config.items('milvus')) 已弃用
debug = _config.getboolean('other', 'debug')
proxy = _config.get('other', 'proxy')

action_plugin = _config.getboolean('plugin', 'action')
schedule_plugin = _config.getboolean('plugin', 'schedule')
speech_plugin = _config.getboolean('plugin', 'speech')
corpus_plugin = _config.getboolean('plugin', 'corpus')
knowledge_plugin = _config.getboolean('plugin', 'knowledge')

try:
    live2D_actions = []
    live2D_embeddings = []
    if action_plugin:
        with open(cfg('action.json'), 'r') as load_f:
            live2D_action_dict = json.load(load_f)
        live2D_actions = live2D_action_dict.keys()
        if not live2D_actions:
            print('action.json为空！')
        live2D_embeddings = [live2D_action_dict[action] for action in live2D_actions]
except FileNotFoundError as e:
    print('读取embedding文件错误，请检查本地是否生成action.json 且动作不为空， 使用action plugin前请先运行 python manager.py action', e)


with open(cfg('forbidden_words.txt'), mode='r', encoding='utf-8') as f:
    keyword_str_list = [line.strip() for line in f.readlines()]

with open(cfg('bili_events.json'), mode='r', encoding='utf-8') as load_f:
    bili_room_event_config_dict = json.load(load_f)

with open(cfg('dy_events.json'), mode='r', encoding='utf-8') as load_f:
    dy_room_event_config_dict = json.load(load_f)

with open(cfg('schedule.json'), mode='r', encoding='utf-8') as load_f:
    old_schedule_event_dict = json.load(load_f)
    schedule_event_dict = {
        schedule_name: data_dict
        for schedule_name, data_dict in old_schedule_event_dict.items()
        if data_dict['switch'] is True
    }

with open(cfg("knowledge.json"), 'r', encoding='utf-8') as f:
    knowledge_cfg_dict = json.load(f)

top_k = 4

event_config_dict = {
    **bili_room_event_config_dict,
    **dy_room_event_config_dict,
    # **schedule_event_dict 定时任务提前处理
}
if __name__ == '__main__':
    print('api_key', proxy)

