from sqlalchemy import Column, String, Boolean, Integer

from src.db.mysql import Base, engine, get_session


class TieBa(Base):

    __tablename__ = "tie_ba"

    id = Column(Integer, primary_key=True)
    hash_id = Column(String(30), nullable=False, unique=True)
    tid = Column(String(20), nullable=False)
    content = Column(String(200), nullable=False)
    embedding_state = Column(Boolean, default=False)
    # embedding = Column(ARRAY, nullable=False)

    def __repr__(self):
        return f'{self.hash_id} self.{self.content}'


if __name__ == '__main__':
    # Base.metadata.create_all(engine)
    # print('over')

    with get_session() as s:
        r_list = s.query(TieBa).limit(3).all()
        for r in r_list:
            print(r.content)