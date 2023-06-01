# 项目名称

GPT-vup

## :memo: 简介

支持BiliBili和抖音直播，基于生产者-消费者模型设计，使用了openai嵌入、GPT3.5 api

![Snipaste_2023-04-25_21-26-54](https://raw.githubusercontent.com/jiran214/GPT-vup/master/public/Snipaste_2023-04-25_21-26-54.png)

## :cloud: 环境

- python 3. 8
- windows
- 确保有VPN 并开启全局代理

## :computer: 功能

1. 回答弹幕和SC
2. 欢迎入场观众
3. 感谢礼物
4. 自定义任务
5. plugin 在config.ini设置，默认都为False
  - speech：监听ctrl+t热键，输入语音转为文本和ai数字人交互
  - action：根据观众的行为匹配对应人物动作
  - schedule：隔一段时间触发某一事件，讲故事、唱rap...

## :book: 原理

![Snipaste_2023-04-25_17-48-51](https://raw.githubusercontent.com/jiran214/GPT-vup/master/public/Snipaste_2023-04-25_17-48-51.png)

GPT-vup一共运行三个子线程：

生产者线程一：BiliBili Websocket

- 运行bilibili_api库，通过长连接websocket不断获取直播间的Event，分配到每个filter函数。
- filter函数干两件事，筛选哪些event入队，入哪个队列
- 线程消息队列有两个：
  - 前提：生产者的生产速度远大于消费者
  - event_queue：有最大长度，超过长度时挤掉最旧的消息，因此它是不可靠的，用来处理直播间的一般消息（普通弹幕、欢迎提示）
  - hight...queue：不限长，处理直播间重要消息（sc、上舰）

生产者线程二：抖音 WebSocket

- 借助开源项目 [抖音弹幕抓取数据推送: 基于系统代理抓包打造的抖音弹幕服务推送程序](https://gitee.com/haodong108/dy-barrage-grab/tree/V2.6.5/BarrageGrab) 在本地开一个转发端口
- 再运行一个线程监听这个端口即可，同样用filter过滤，入队

生产者线程三：

- 如果vup只有回应弹幕，我觉得有些单调了，因此可以通过schedule模块，每隔一段时间往high_priority_event_queue送一些自定义Event，比如我想让她每隔十分钟做一个自我介绍、表演节目。
- 5-13更新，支持热键触发实时语音交互，见plugin

消费者线程：

- worker类，有三个函数：generate_chat、generate_action、output去处理不同的Event
- 遵循依赖倒置原则，不管弹幕Event、sc Event都依赖抽象Event，而worker也依赖Event

说明：
- 消费者线程必须运行，生产者线程保证至少一个开启

## :microscope: 安装配置及使用教程

### 克隆项目，安装python依赖

```
git https://github.com/jiran214/GPT-vup.git
cd src
# 建议命令行或者pycharm创建虚拟环境并激活
python -m pip install --upgrade pip pip
# 可能会依赖冲突，没法彻底解决
pip install -r .\requirements.txt --no-deps
```

### 配置config

在src目录下创建配置文件config.ini(该项目所有配置信息都在这)

```ini
[openai]
api_key = sk-iHeZopAaLtem7E7FLEM6T3BaakFJsvhz0yVchBkii0oLJl0V

[room]
id=27661527

[edge-tss]
voice = zh-CN-XiaoyiNeural
rate = +10%
volume = +0%

[other]
debug = True
proxy = 127.0.0.1:7890

[plugin]
action=False
schedule=False
speech=False
```

**说明：**

- room-id 为直播间房，比如我的是[哔哩哔哩直播，二次元弹幕直播平台 (bilibili.com)](https://live.bilibili.com/27661527)最后一部分（没有房间号可以随便找一个作为测试）

- edge-tss 语音相关配置

### 安装VTS（Vtuber Studio），获取VTS TOKEN并调试API

- 安装及使用教程网上有，可以配置嘴和音频同步，只说明程序部分
- action plugin 实现Vtuber根据观众的互动行为匹配动作，可忽略
  - config.ini 中的action设置为True
  - 打开VTS，开启VTS的API开关
  - 给任务的每一个动作重命名为体现动作表情的词，不然没有意义
  - 运行>> `python ./main action`，pyvts会请求vts api（注意：此时VTS会有确认弹窗）
  - 会自动生成 action.json


说明：action plugin原理？

- 简单说 根据用户发来的弹幕响应对应的动作，先去获取弹幕或者相关信息的向量，用这个向量查找action_embeddings中余弦相似度最接近的向量，也就是最接近的动作，作为响应action。
- 动作响应不一定依靠embedding，实际效果差强人意，用embedding是因为我有考虑到 后期可以给用户的输入匹配更多上下文。上下文可以来源于任何地方 贴吧、小红书...只要提前生成向量保存到向量数据库即可，让AI主播的回答更丰富。
- 关于openai的embedding的介绍和作用，可以看openai文档 [Embeddings - OpenAI API](https://platform.openai.com/docs/guides/embeddings)

### 抖音直播配置（可忽略）

- 参考 [抖音弹幕抓取数据推送: 基于系统代理抓包打造的抖音弹幕服务推送程序](https://gitee.com/haodong108/dy-barrage-grab/tree/V2.6.5/BarrageGrab) 
- 打开正在直播的直播间，数据开始抓取

### 运行

- 方式一：谷歌fire库 命令行方式启动（默认）：确保 main.py fire.Fire(Management)这一行运行，其它注释掉
- 方式二：正常运行，根据需要运行
  ```python
  if __name__ == '__main__':
    """命令行启动，等同于下面的程序启动"""
    # fire.Fire(Management)

    """测试"""
    # >> python main test
    # Management().test()

    """启动程序"""
    # >> python main run bilibili
    # Management().run('BiliBili')
    # Management().run('DouYin')

    """初始化"""
    # >> python main action
    # Management().action()
  ```
- 建议先运行测试，检测vpn，再正式运行程序
- python main action 时用来初始化 action plugin的，可忽略

### OBS

网上有教程

## :bulb: 踩坑和经验

1. 再用openai库的acreate 关闭ssl还是会偶尔遇到ssl报错，怀疑lib底层调aiohttp有冲突，使用create后报错明显减少
2. 和vts交互上，最开始尝试keyboard键盘操作操控，发现vts的快捷键不像其它软件一样，只能通过pyvts调用api实现动作响应
3. 在这个AI主播的场景里，需要确保每个 消息队列出队-处理-输出过程的原子性，最好不要同时处理多个弹幕（Event）
4. 协程适合轻量级的任务，或者说一个协程函数里awiat不能太多，否则并发安全很难维护
5. 每个线程要创建自己的事件循环
6. 本项目利用协程解耦不同的生产消费过程，也可以看看这篇文章[写个AI虚拟主播：看懂弹幕，妙语连珠，悲欢形于色，以一种简单的实现 - 掘金 (juejin.cn)](https://juejin.cn/post/7204742468612145209)，它用到端口/进程解耦，最后把所有组件用Go组装，AI 主播 总体流程都差不多

## :page_with_curl: 更新日志

- 4.26 支持抖音直播
- 5.13 LangChain重构prompt部分
- 5.13 config.json存取action及向量
- 5.13 支持通过fire命令行启动
- 5.13 增加运行前的测试
- 5.13 插件系统
- 5.14 requirements 修改，bilibili_api库没有更新，没法彻底解决依赖，请在pip install后面加上--no-deps

## :phone: Contact Me

欢迎加我WX：yuchen59384 交流！
