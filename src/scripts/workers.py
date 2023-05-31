from bilibili_api import sync
from pymilvus import FieldSchema, Collection, CollectionSchema, DataType, has_collection

from src import config
from src.db.mysql import get_session
from src.scripts.models import TieBa
from src.utils.init import initialize_openai
from src.utils.utils import sync_get_embedding


class EmbeddingWorker:

    def __init__(self, limit_num=100, embedding_query_num=5000):
        try:
            from pymilvus import FieldSchema, DataType
            from pymilvus import connections
        except:
            raise 'Please run pip install pymilvus==2.1'

        initialize_openai()
        connections.connect(
            alias="default",
            host=config.milvus['host'],
            port=config.milvus['port']
        )

        self.limit_num = limit_num
        self.embedding_query_max_length = embedding_query_num

    def search_rows_no_embedding(self, model: TieBa):
        while 1:
            with get_session() as s:
                rows = s.query(model).filter(model.embedding_state == False).limit(self.limit_num).all()
                if not rows:
                    break
                rows_no_embedding = []
                rows_content_list = []
                current_length = 0
                while 1:
                    if rows:
                        row = rows.pop()
                        rows_no_embedding.append(row)
                        rows_content_list.append(row.content)
                        current_length += len(row.content)
                    else:
                        break
                    if current_length > self.embedding_query_max_length or not rows:
                        yield rows_no_embedding, rows_content_list
                        rows_no_embedding = []
                        rows_content_list = []
                        current_length = 0

    def query_embedding(self, rows_no_embedding, rows_content_list):
        embedding = sync_get_embedding(rows_content_list)
        # content = rows_content_list
        hash_id = [int(row.hash_id) for row in rows_no_embedding]
        return [hash_id, embedding]

    @staticmethod
    def create_collection(name, desc):
        # 创建集合
        hash_id = FieldSchema(
            name="hash_id",
            dtype=DataType.INT64,
            is_primary=True,
        )
        # content = FieldSchema(
        #     name="content",
        #     dtype=DataType.VARCHAR,
        # )
        embedding = FieldSchema(
            name="embedding",
            dtype=DataType.FLOAT_VECTOR,
            dim=1536
        )
        schema = CollectionSchema(
            fields=[hash_id, embedding],
            description=desc
        )
        collection_name = name
        collection = Collection(
            name=collection_name,
            schema=schema,
            using='default',
            shards_num=2,
            consistency_level="Strong"
        )
        return collection

    @staticmethod
    def create_index(collection):
        # 创建索引
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }
        collection.create_index(
            field_name="embedding",
            index_params=index_params
        )

    @staticmethod
    def push_2_milvus(collection, entries):
        # 插入数据
        try:
            collection.insert(entries)
            print(f'插入成功，共{len(entries[0])}条')
            return True
        except Exception as e:
            print('插入失败')
            raise e
            return False

    def run(self, name, desc, model):
        if not has_collection(name):
            collection = self.create_collection(name, desc)
            self.create_index(collection)
        else:
            collection = Collection(name)

        for rows_no_embedding, rows_content_list in self.search_rows_no_embedding(model):
            entries = self.query_embedding(rows_no_embedding, rows_content_list)
            if self.push_2_milvus(collection, entries):
                with get_session() as s:
                    for tie in rows_no_embedding:
                        tie.embedding_state = True
            print('over')


if __name__ == '__main__':
    EmbeddingWorker().run('sun_ba', '孙笑川吧', TieBa)

    # data = [['-498603715 你没事吧，这一看就是你们男宝反串的。你怎么自挂东南枝？']]