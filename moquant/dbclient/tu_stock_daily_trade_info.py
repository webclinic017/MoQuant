' Declaration of table `tu_stock_daily_trade_info` '
__author__ = 'Momojie'

from sqlalchemy import Column, Integer, String, DECIMAL
from moquant.dbclient.base import Base


class StockDailyInfo(Base):
    __tablename__ = 'tu_stock_daily_trade_info'

    ts_code = Column('ts_code', String(10), primary_key=True)
    trade_date = Column('trade_date', String(10), primary_key=True)
    open = Column('open', DECIMAL(30, 10))
    high = Column('high', DECIMAL(30, 10))
    low = Column('low', DECIMAL(30, 10))
    close = Column('close', DECIMAL(30, 10))
    pre_close = Column('pre_close', DECIMAL(30, 10))
    change = Column('change', DECIMAL(30, 10))
    pct_chg = Column('pct_chg', DECIMAL(30, 10))
    vol = Column('vol', DECIMAL(30, 10))
    amount = Column('amount', DECIMAL(30, 10))


def create(engine):
    Base.metadata.create_all(engine)
