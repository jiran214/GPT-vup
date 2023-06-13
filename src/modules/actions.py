"""
 @Author: jiran
 @Email: jiran214@qq.com
 @FileName: action.py
 @DateTime: 2023/4/24 0:01
 @SoftWare: PyCharm
"""
from src.config import live2D_actions

plugin_info = {
    "plugin_name": "start pyvts",
    "developer": "Jiran",
    "authentication_token_path": "./token.txt"
}


async def play_action(action_name: str):
    try:
        import pyvts
    except ImportError:
        raise 'Please run pip install pyvts'
    vts = pyvts.vts(plugin_info=plugin_info)
    await vts.connect()
    await vts.read_token()
    await vts.request_authenticate()  # use token

    if action_name not in live2D_actions:
        raise ValueError(f'动作不存在：{action_name}')
    send_hotkey_request = vts.vts_request.requestTriggerHotKey(action_name)
    await vts.request(send_hotkey_request)
    await vts.close()


if __name__ == "__main__":
    action_embeddings = None  # 获取token不需要运行
    # asyncio.run(initialize_action())
    # asyncio.run(play_action())
