PREFIX = (
    "Answer the following questions as best you can. "
    "You have the permission to query the information you need from the following knowledge base:"
)

FORMAT_INSTRUCTIONS = """Use the following format:

Question: the input question that you have to answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{knowledge_base_names}]
Action Input: the input to the action"""

SUFFIX = """Begin!

Question: {input}
Thought:{agent_scratchpad}"""

