import enum


class TxtMode(enum.Enum):
    GPT3dot5 = 'ChatGPT-3.5'
    DIRECTLY = '直接生成语音'
    # GPT3 = 'ChatGPT-3'
    # 一下两个需要二次判断
    CORPUS = '本地语料库'
    KNOWLEDGE_BASE = '本地知识库'


class ActionMode(enum.Enum):
    Embedding = '相似度'
    FIXED_ACTION = '指定动作'
    FROM_GPT = 'GPT返回动作词'
    NONE = None
