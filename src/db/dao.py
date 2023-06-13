import contextlib

from sqlalchemy.orm import Session
import contextlib
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import (
    create_engine
)
from src import config  # config模块里有自己写的配置，我们可以换成别的，注意下面用到config的地方也要一起换

engine = create_engine(
    config.sqlite['uri'] or config.mysql['uri'],  # SQLAlchemy 数据库连接串
    # echo=bool(config.SQLALCHEMY_ECHO),  # 是不是要把所执行的SQL打印出来，一般用于调试
    # pool_size=int(config.SQLALCHEMY_POOL_SIZE),  # 连接池大小
    # max_overflow=int(config.SQLALCHEMY_POOL_MAX_SIZE),  # 连接池最大的大小
    # pool_recycle=int(config.SQLALCHEMY_POOL_RECYCLE),  # 多久时间回收连接
)
session = sessionmaker(bind=engine)
Base = declarative_base(engine)


@contextlib.contextmanager
def get_session() -> Session:
    s = session()
    try:
        yield s
        s.commit()
    except Exception as e:
        s.rollback()
        raise e
    finally:
        s.close()
