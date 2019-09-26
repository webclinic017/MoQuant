""" Declaration of table `mq_stock_mark` """

from sqlalchemy import Column, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class MqStockMark(Base):
    __tablename__ = 'mq_stock_mark'

    ts_code = Column('ts_code', String(10), primary_key=True, comment='ts代码')
    last_handle_date = Column('last_handle_date', String(10), comment='最后处理日期')
    fetch_data = Column('fetch_data', Boolean, comment='是否拉取数据')


def create(engine):
    Base.metadata.create_all(engine)
