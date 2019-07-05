' Declaration of table `stock_daily_info` '
__author__ = 'Momojie'

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, DECIMAL
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class StockDailyInfo(Base):
    __tablename__ = 'stock_daily_trade_info'

    ts_code = Column('ts_code', String(10), primary_key=True)
    trade_date = Column('trade_date', String(10), primary_key=True)
    open = Column('open', DECIMAL(10, 2))
    high = Column('high', DECIMAL(10, 2))
    low = Column('low', DECIMAL(10, 2))
    close = Column('close', DECIMAL(10, 2))
    pre_close = Column('pre_close', DECIMAL(10, 2))
    change = Column('change', DECIMAL(10, 2))
    pct_chg = Column('pct_chg', DECIMAL(10, 2))
    vol = Column('vol', DECIMAL(10, 2))
    amount = Column('amount', DECIMAL(10, 2))

    def __repr__(self):
        return 'code: %s, date: %s' % (self.ts_code, self.trade_date)
