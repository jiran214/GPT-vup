"""
 @Author: jiran
 @Email: jiran214@qq.com
 @FileName: speech_recognition.py
 @DateTime: 2023/5/13 18:21
 @SoftWare: PyCharm
"""
import time

import pyaudio
import wave
import speech_recognition as sr
import keyboard

# 定义参数
from src.utils.utils import UserEvent
from src.utils.utils import request_logger
from src.utils.utils import user_queue

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "./static/speech/{}.wav"

logger = request_logger


def speech_recognition_task():
    r = sr.Recognizer()

    # 使用PyAudio录制音频
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    frames = []
    print("正在录音...")
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
        # if keyboard.is_pressed('ctrl+t'):  # 按下Ctrl+T停止录音
        #     break
    print("录音结束")

    stream.stop_stream()
    stream.close()
    audio.terminate()

    # 将录制的音频写入Wave文件
    waveFile = wave.open(WAVE_OUTPUT_FILENAME.format(int(time.time())), 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(audio.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()

    try:
        # 使用SpeechRecognition库来将音频转换为文本(非常慢)
        audio_file = sr.AudioFile(WAVE_OUTPUT_FILENAME.format(int(time.time())))

        with audio_file as source:
            audio_data = r.record(source)
            logger.debug('正在请求语音转文字接口recognize_google...')
            text = r.recognize_google(audio_data, language='zh-CN')

            ue = UserEvent(text, '{}')
            ue.is_high_priority = True
            # ue.action = live2D_actions.index('Anim Shake')
            user_queue.send(ue)
    except sr.UnknownValueError:
        print("无法识别语音")
    except sr.RequestError as e:
        print(f"语音识别服务出错：{e}")


def speech_hotkey_listener():
    keyboard.add_hotkey('ctrl+t', speech_recognition_task)


if __name__ == '__main__':
    speech_hotkey_listener()
