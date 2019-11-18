from sqlalchemy import Column, String, DECIMAL, BIGINT, Index

from moquant.dbclient.base import Base


class TsStkLimit(Base):
    __tablename__ = 'ts_stk_limit'
    __table_args__ = (
        Index('code', 'ts_code'),
        Index('date', 'trade_date'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    id = Column('id', BIGINT, primary_key=True, comment='id', autoincrement=True)
    trade_date = Column('trade_date', String(10), comment='交易日期')
    ts_code = Column('ts_code', String(10), comment='TS股票代码')
    up_limit = Column('up_limit', DECIMAL(30, 10), comment='涨停价')
    down_limit = Column('down_limit', DECIMAL(30, 10), comment='跌停价')
