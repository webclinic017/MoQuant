' Declaration of table `tu_stock_daily_trade_info` '
__author__ = 'Momojie'

from sqlalchemy import Column, Integer, String, DECIMAL
from moquant.dbclient.base import Base


class StockDailyInfo(Base):
    __tablename__ = 'tu_stock_daily_trade_info'

    ts_code = Column('ts_code', String(10), primary_key=True)
    trade_date = Column('trade_date', String(10), primary_key=True)
    open = Column('open', DECIMAL(18, 2))
    high = Column('high', DECIMAL(18, 2))
    low = Column('low', DECIMAL(18, 2))
    close = Column('close', DECIMAL(18, 2))
    pre_close = Column('pre_close', DECIMAL(18, 2))
    change = Column('change', DECIMAL(18, 2))
    pct_chg = Column('pct_chg', DECIMAL(18, 2))
    vol = Column('vol', DECIMAL(18, 2))
    amount = Column('amount', DECIMAL(18, 2))


def create(engine):
    Base.metadata.create_all(engine)
