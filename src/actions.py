"""
 @Author: jiran
 @Email: jiran214@qq.com
 @FileName: action.py
 @DateTime: 2023/4/24 0:01
 @SoftWare: PyCharm
"""
import asyncio

import pyvts

from src.opanAi import async_get_embedding, sync_get_embedding
from src.log import worker_logger

logger = worker_logger


live2D_actions = ['Heart Eyes', 'Eyes Cry', 'Angry Sign', 'Shock Sign', 'Remove Expressions', 'Anim Shake', 'Sad Shock']
live2D_action_emotions = ['Heart Eyes', 'Eyes Cry', 'Angry Sign', 'Shock Sign', 'Remove Expressions', 'Anim Shake', 'Sad Shock']

logger.debug('live2D_action_emotions向量中...')
action_embeddings = sync_get_embedding(live2D_action_emotions)

plugin_info = {
    "plugin_name": "start pyvts",
    "developer": "Jiran",
    "authentication_token_path": "./token.txt"
}


async def play_action(action_index):
    vts = pyvts.vts(plugin_info=plugin_info)
    await vts.connect()
    await vts.read_token()
    await vts.request_authenticate()  # use token

    if action_index > len(live2D_actions) - 1:
        raise '动作不存在'
    logger.debug(f'Live2D action:{live2D_actions[action_index]}')
    send_hotkey_request = vts.vts_request.requestTriggerHotKey(live2D_actions[action_index])
    await vts.request(send_hotkey_request)
    await vts.close()


async def initialize_action():
    # websocket连接 获取token到本地
    vts = pyvts.vts(plugin_info=plugin_info)
    await vts.connect()
    logger.debug('获取live2D VTS...请确认！')
    await vts.request_authenticate_token()  # get token
    await vts.write_token()
    # await vts.read_token()
    await vts.request_authenticate()  # use token

    # 获取vts所有模型动作
    response_data = await vts.request(vts.vts_request.requestHotKeyList())
    hotkey_list = []
    for hotkey in response_data['data']['availableHotkeys']:
        hotkey_list.append(hotkey['name'])
    print('所有模型动作', hotkey_list)

    # 测试
    assert hotkey_list == live2D_actions  # vts 和 本地的动作是否一致
    assert len(hotkey_list) not in (0, 1)  # 动作太少
    send_hotkey_request = vts.vts_request.requestTriggerHotKey(live2D_actions[1])
    await vts.request(send_hotkey_request)

    # print(action_embeddings)
    await vts.close()


if __name__ == "__main__":
    action_embeddings = None  # 获取token不需要运行
    asyncio.run(initialize_action())
    # asyncio.run(play_action())
