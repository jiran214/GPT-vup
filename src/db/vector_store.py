import os.path
from typing import List

import qdrant_client
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.schema import Document
from langchain.vectorstores import Qdrant

from src.config import root_path
from src.utils.utils import get_openai_key


embeddings = OpenAIEmbeddings(openai_api_key=get_openai_key())


def similarity_search_from_qdrant(query, collection_name, k: int = 4):

    # embeddings.openai_api_key = get_openai_key()
    client = qdrant_client.QdrantClient(
        path=os.path.join(root_path, "db/Qdrant"), prefer_grpc=True
    )
    qdrant = Qdrant(
        client=client, collection_name=collection_name,
        embeddings=embeddings
    )
    found_docs = qdrant.similarity_search_with_score(
        query,
        k=k
    )
    return found_docs


if __name__ == '__main__':
    res = similarity_search_from_qdrant(query="四号", collection_name="test111.txt", k=20)
    for r in res:
        print(r[0])
        print(r[1])