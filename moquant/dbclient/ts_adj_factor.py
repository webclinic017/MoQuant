' Declaration of table `ts_adj_factor` '

from sqlalchemy import Column, String, DECIMAL

from moquant.dbclient.base import Base


class AdjFactor(Base):
    __tablename__ = 'ts_adj_factor'

    ts_code = Column('ts_code', String(10), primary_key=True, comment='ts代码')
    trade_date = Column('trade_date', String(10), primary_key=True, comment='交易日期')
    adj_factor = Column('adj_factor', DECIMAL(30, 10), comment='复权因子')


def create(engine):
    Base.metadata.create_all(engine)
