# GPT-vup Live2D数字人直播

![](https://img.shields.io/badge/license-GPL-blue)

## 简介
**Real Virtual UP**
支持BiliBili和抖音直播，基于生产者-消费者模型设计，使用了openai嵌入、GPT3.5 api

### 功能
- 基本功能，回答弹幕和SC、欢迎入场观众、感谢礼物
- plugin(默认关闭)
  - speech：监听ctrl+t热键，输入语音转为文本和ai数字人交互
  - action：根据观众的行为匹配对应人物动作
  - schedule：隔一段时间触发某一事件，讲故事、唱rap...
  - context：给问题补充上下文
## 安装
### 环境
- win 10
- python 3.8
- vpn全局代理
### pip安装依赖
```shell
git clone https://github.com/jiran214/GPT-vup.git
cd src
# 建议命令行或者pycharm创建虚拟环境并激活 https://blog.csdn.net/xp178171640/article/details/115950985
python -m pip install --upgrade pip pip
pip install -r .\requirements.txt
```
### 新建config.ini 
- 重命名config.sample.ini为config.ini
- 更改api_key和proxy 其它可以不用管
- 相关配置见后
### 测试网络环境
- src目录下运行：>>`python manager.py test_net`
## 快速开始
### B站直播
- 安装依赖库：>>`pip install bilibili_api --no-deps`
- config.ini 的 room -> id 更改为自己的房间号，可以先随便找个
- src目录下运行：>>`python manager.py run bilibili`
### 抖音直播
- 参考 [抖音弹幕抓取数据推送: 基于系统代理抓包打造的抖音弹幕服务推送程序](https://gitee.com/haodong108/dy-barrage-grab/tree/V2.6.5/BarrageGrab) 
- 启动该项目
- 打开web或者桌面端抖音正在直播的直播间，数据开始抓取
- src目录下运行：>>`python manager.py run douyin`
### Vtube Studio 安装及配置
- 在steam下载Vtube Studio软件
- 教程：https://www.bilibili.com/video/BV1nV4y1X7yJ?t=426.7
- 重点！！！
  - 麦克风设置：你可以不用虚拟声道，win 默认输出设备为Speaker Realtek(R) Audio，在VTS里的麦克风设置，输入设备也设置为Realtek(R) Audio即可。
  - 嘴型同步声音，在mouthOpen的输入参数设置为声音频率、或者声音音量
- 如果需要更好的直播效果，请自行了解更多
## 进阶
### speech plugin：语音交互
- config.ini -> plugin -> speech 设置为True
- 运行>> `pip install pyaudio speech_recognition keyboard`
- 程序启动后按住 ctrl+T 说话，自动语音转文字，vup会听到你说的话
### schedule plugin：隔一段时间触发某一事件，讲故事、唱rap...
- config.ini -> plugin -> schedule 设置为True
- utils/prompt_temple.py 的schedule_task_temple_list列表有我写好的触发事件
### action plugin：VTS动作表情交互
实现vup根据观众的互动行为匹配动作
- config.ini -> plugin -> action设置为True
- 运行>>`pip install pyvts`
- 打开VTS，开启VTS的API开关
- 在VTS的表情设置里，给每一个动作重命名为体现动作表情的词，不然没有意义
- src目录下运行>> `python manager.py action`，pyvts会请求vts api（注意：此时VTS会有确认弹窗）
- 程序会自动生成 action.json
- 如果需要更新动作，请重复上述步骤
### 实验功能：context plugin：给对话补充上下文
- 前提1：Docker[安装milvus2.0单机版本](https://milvus.io/docs/v2.0.x/install_standalone-docker.md)，并设置 config.ini -> milvus -> host and port
- 前提2：Mysql环境，并设置 config.ini -> mysql -> uri
- config.ini -> plugin -> context 设置为True
- 运行>> `pip install pymilvus==2.0`
- 自行设置scripts/manager.py的参数，运行>> `python scripts/manager.py run`，采集贴吧数据到MySQL，处理后推给Milvus
### 其它
- utils/prompt_temple.py 的 system_template 可以更改vup的初始设定
## 更新日志
- V2.0 支持context plugin，目录重构、更简单的readme，解决依赖混乱的问题
- V1.0 [旧版本内容](https://github.com/jiran214/GPT-vup/tree/1.0)
## to do list
- [ ] speech plugin 阻塞问题
- [ ] context plugin优化
- [ ] 本地模型替换api请求
## Contact Me
- 请先star本项目~~
- **如果你遇到各种问题，请提issues，一般的问题不要加我，感谢理解！**
- 欢迎加我WX：yuchen59384 交流！
- ![](https://github.com/jiran214/GPT-vup/blob/2.0/public/mm_reward_qrcode_1686025672796.png)
