import os
from typing import List

from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader, PyPDFLoader
from langchain.vectorstores import Qdrant

from src.config import root_path
from src.utils.log import worker_logger
from src.utils.utils import get_openai_key

db_location = "db/Qdrant"
docs_location = "static/documents/{}"
logger = worker_logger

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=0,
    separators=["\n", "。", " ", ""],
    length_function=len
)

pdf_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    separators=["\n\n", "\n", "。", " ", ""],
    length_function=len
)


class Loader:

    def __init__(self, file_name):
        self.file_name = file_name
        self.file_extension = file_name.split(".")[-1]

    def load_pdf(self) -> List[Document]:
        loader = PyPDFLoader(os.path.join(root_path, docs_location.format(self.file_name)))
        pages = loader.load_and_split(text_splitter=pdf_splitter)
        return pages

    def load_txt(self) -> List[Document]:
        loader = TextLoader(os.path.join(root_path, docs_location.format(self.file_name)), encoding='utf-8')
        documents = loader.load()
        docs = text_splitter.split_documents(documents)
        return docs

    def load(self):
        load_func = getattr(self, f'load_{self.file_extension}', None)
        if load_func:
            return load_func()
        else:
            logger.warning('暂时不支持该类型文件')


def save_2_qdrant(collection_name, docs: List[Document]):
    embeddings = OpenAIEmbeddings(openai_api_key=get_openai_key())
    qdrant = Qdrant.from_documents(
        docs, embeddings,
        path=os.path.join(root_path, db_location),
        collection_name=collection_name
    )