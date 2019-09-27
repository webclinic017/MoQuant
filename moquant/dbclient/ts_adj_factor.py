""" Declaration of table `ts_adj_factor` """

from sqlalchemy import Column, String, DECIMAL, BIGINT, Index

from moquant.dbclient.base import Base


class StockAdjFactor(Base):
    __tablename__ = 'ts_adj_factor'
    __table_args__ = (
        Index('code_date', 'ts_code', 'trade_date'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    id = Column('id', BIGINT, primary_key=True, comment='id', autoincrement=True)
    ts_code = Column('ts_code', String(10), comment='ts代码')
    trade_date = Column('trade_date', String(10), comment='交易日期')
    adj_factor = Column('adj_factor', DECIMAL(30, 10), comment='复权因子')


def create(engine):
    Base.metadata.create_all(engine)
