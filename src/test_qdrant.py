from langchain import OpenAI
from langchain.agents import create_vectorstore_router_agent
from langchain.agents.agent_toolkits import (
    create_vectorstore_agent,
    VectorStoreToolkit,
    VectorStoreInfo, VectorStoreRouterToolkit,
)

import qdrant_client
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Qdrant

from src.config import root
from src.utils.utils import get_openai_key


embeddings = OpenAIEmbeddings(openai_api_key=get_openai_key())
llm = OpenAI(temperature=0, openai_api_key=get_openai_key())

client = qdrant_client.QdrantClient(
        path=root("db/Qdrant"), prefer_grpc=True
)

qdrant = Qdrant(
    client=client, collection_name="test_pdf.pdf",
    embeddings=embeddings
)

vector_store_info = VectorStoreInfo(
    name="香蕉知识库",
    description="2号链接；可以购买，有优惠，物美价廉",
    vectorstore=qdrant
)

vector_store_info2 = VectorStoreInfo(
    name="苹果知识库",
    description="高端人士",
    vectorstore=qdrant
)

toolkit = VectorStoreToolkit(vectorstore_info=vector_store_info, llm=llm)
agent_executor = create_vectorstore_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True
)

# router_toolkit = VectorStoreRouterToolkit(
#     vectorstores=[vector_store_info, vector_store_info2],
#     llm=llm
# )

# agent_executor = create_vectorstore_router_agent(
#     llm=llm,
#     toolkit=router_toolkit,
#     verbose=True
# )

agent_executor.run('3号链接怎么卖的')