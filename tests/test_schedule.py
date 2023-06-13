import json
import os
import time
from datetime import datetime, timedelta

from src import config
from src.config import root
from src.core.main import start_thread


sound_base_path = root('static/voice/{}.mp3')


def test_schedule_construct(capsys):

    config.schedule_plugin = True
    now = datetime.now()
    future_time = now + timedelta(seconds=60)
    time_str = future_time.strftime('%H:%M')
    print('time_str', time_str)
    cfg_dict = """{
  "schedule_name1": {
    "switch": true,
    "timing": null,
    "frequency": "0.5",
    "audio_txt": "你好呀",
    "action": {
      "name": null
    }
  },
  "schedule_name2": {
    "switch": true,
    "timing": "%s",
    "frequency": null,
    "audio_txt": "你好呀",
    "action": {
    "name": null
    }
  }
}"""
    config.schedule_event_dict = json.loads(cfg_dict % time_str)
    start_thread('user_producer')
    # time.sleep(30)
    assert os.path.exists(sound_base_path.format('schedule_name1'))
    assert os.path.exists(sound_base_path.format('schedule_name2'))
    start_thread('consumer')
    time.sleep(60)
    # 检查输出是否包含特定的字符串
    captured = capsys.readouterr()
    assert "audio_txt1" in captured.out
    assert "audio_txt2" in captured.out

    os.unlink(sound_base_path.format('schedule_name1'))
    os.unlink(sound_base_path.format('schedule_name2'))
