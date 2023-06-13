from langchain import OpenAI
import json

from src import config
from src.utils.utils import get_openai_key

prompt_temple = """
我遇收到了一个<消息>，尽可能帮助我选择一个工具尝试去搜索更多信息。
如果工具描述和<消息>有较大的相关性则选择这个工具,工具如下：

{tools}

你只需要输出一个json格式,如下：
```json
    {{{
        "工具名称": string // 字段值为[香蕉知识库、苹果知识库、蔬菜知识库]的一个，如果以上工具和<消息>关联性低，则输出"未知"在这
        "工具输入": string // 用来查询更多信息的输入
    }}}
```
你的回答除了上面的内容外，一定不能出现任何其它文本,

Begin!

消息：{message}
"""


llm = OpenAI(temperature=0, openai_api_key="temp")
tools = ''.join([
    f"""
    工具名称：{tool_name}知识库
    工具描述：{tool_dict['desc']}
    
    """ for tool_name, tool_dict in config.knowledge_cfg_dict.items()
])


def get_knowledge_base_info(message):
    prompt = prompt_temple.format(
        tools=tools,
        message=message
    )
    llm.openai_api_key = get_openai_key()
    llm_res = llm.generate([prompt])
    assistant_content = llm_res.generations[0][0].text
    return assistant_content
