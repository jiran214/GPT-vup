import fire

from src.db.models import *
from src.db.mysql import Base, engine
from src.scripts.crawlers.tie_ba_spider import Ba
from src.scripts.workers import EmbeddingWorker


class Management:
    @staticmethod
    def create():
        Base.metadata.create_all(engine)

    @staticmethod
    def crawl(kw='孙笑川', max_ba_pn=1, max_tie_pn=1, start_ba_pn=1, start_tie_pn=1, max_str_length=400):
        Ba(kw, max_ba_pn, max_tie_pn, start_ba_pn, start_tie_pn, max_str_length).depth_first_run()

    @staticmethod
    def embedding(name='sun_ba', desc='孙笑川吧', *, model: Document):
        EmbeddingWorker(limit_num=100, embedding_query_num=5000).run(name, desc, model)

    def run(self):
        self.create_table()
        self.crawl()
        self.embedding(model=TieBa)


if __name__ == '__main__':
    fire.Fire(Management)
