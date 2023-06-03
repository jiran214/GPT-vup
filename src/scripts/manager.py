import fire

from src.db.models import *
from src.db.mysql import Base, engine
from src.scripts.crawlers.tie_ba_spider import Ba
from src.scripts.workers import EmbeddingWorker


class Management:
    @staticmethod
    def create_table():
        Base.metadata.create_all(engine)

    @staticmethod
    def crawl(kw='孙笑川', max_ba_pn=1, max_tie_pn=1, start_ba_pn=1, start_tie_pn=1, max_str_length=400):
        """

        Args:
            kw: 贴吧吧名
            max_ba_pn: 贴吧最大爬取页数
            max_tie_pn: 每个帖子最大页数
            start_ba_pn: 吧开始页数
            start_tie_pn: 开始帖子页数
            max_str_length: 接受最短的文本长度

        Returns:

        """
        Ba(kw, max_ba_pn, max_tie_pn, start_ba_pn, start_tie_pn, max_str_length).depth_first_run()

    @staticmethod
    def embedding(name, model, desc=''):
        """

        Args:
            name: Milvus集合名
            model: 定义mysql模型，需要继承于Document
            desc: 集合简介

        Returns:

        """
        EmbeddingWorker(limit_num=100, embedding_query_num=5000).run(name, desc, model)

    def run(self, kw, name):
        self.create_table()
        self.crawl(kw=kw)
        self.embedding(name, model=TieBa)


if __name__ == '__main__':
    fire.Fire(Management)
