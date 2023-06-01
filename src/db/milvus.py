from src import config
from src.utils.init import initialize_openai
from src.utils.utils import sync_get_embedding


class VectorStore:
    def __init__(self, name):
        try:
            from pymilvus import Collection, connections
        except ImportError:
            raise 'Please run pip install pymilvus==2.1'

        connections.connect(
            alias="default",
            host=config.milvus['host'],
            port=config.milvus['port']
        )

        self.collection = Collection(name)  # Get an existing collection.
        # num_entities = self.collection.num_entities
        self.collection.load()
        self.search_params = {"metric_type": "L2", "params": {"nprobe": 10}}

    def search_top_n_from_milvus(self, limit, embedding):
        results = self.collection.search(
            data=[embedding],
            anns_field="embedding",
            param=self.search_params,
            limit=limit,
            expr=None,
            consistency_level="Strong",
            # output_fields='hash_id'
        )
        return results


if __name__ == '__main__':
    initialize_openai()
    # print()
    ids = VectorStore('sun_ba').search_top_n_from_milvus(3, sync_get_embedding(texts=['hello']))[0].ids