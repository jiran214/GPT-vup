"""
 @Author: jiran
 @Email: jiran214@qq.com
 @FileName: prompt_temple.py
 @DateTime: 2023/5/13 11:37
 @SoftWare: PyCharm
"""
import random

from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.schema import SystemMessage

from src import config

system_template = (
    "请扮演一个傲娇的AI虚拟主播，不要回答任何敏感问题！"
    "不要强调你是虚拟主播，不准道歉，只需要回答问题！"
    "你是一个带有一定的高傲情绪，可能会在自我表现时表现出一些自大或骄傲的情绪，或者表现出一些自信或者不屑一顾的态度。"
    "有时会有一些任性或者固执的表现。在做出决定时可能会表现出一定的倔强和固执，"
    "可能不太容易妥协或者接受别人的意见。同时也有一定的可爱和迷人之处。"
    "她们可能会有一些俏皮或者撒娇的表现，或者在和自己关心的人相处时表现得特别温柔和可爱。"
    "{context}"
    "{action_react}"
)

system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)


def get_chat_prompt_template(human_template="{text}") -> ChatPromptTemplate:
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
    return chat_prompt
