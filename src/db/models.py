from sqlalchemy import Column, String, Boolean, Integer

from src.db.mysql import Base, engine, get_session


class Document(Base):
    id = Column(Integer, primary_key=True)
    hash_id = Column(String(30), nullable=False, unique=True)
    content = Column(String(200), nullable=False)
    embedding_state = Column(Boolean, default=False)

    def __repr__(self):
        return f'{self.hash_id} self.{self.content}'


class TieBa(Document):
    __tablename__ = "tie_ba"
    tid = Column(String(20), nullable=False)

    # embedding = Column(ARRAY, nullable=False)


if __name__ == '__main__':
    # Base.metadata.create_all(engine)
    # print('over')

    with get_session() as s:
        r_list = s.query(TieBa).limit(3).all()
        for r in r_list:
            print(r.content)
