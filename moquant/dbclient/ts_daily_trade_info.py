' Declaration of table `ts_daily_trade_info` '
__author__ = 'Momojie'

from sqlalchemy import Column, Integer, String, DECIMAL
from moquant.dbclient.base import Base


class StockDailyInfo(Base):
    __tablename__ = 'ts_daily_trade_info'

    ts_code = Column('ts_code', String(10), primary_key=True, comment='ts代码')
    trade_date = Column('trade_date', String(10), primary_key=True, comment='交易日期')
    open = Column('open', DECIMAL(30, 10), comment='开盘价')
    high = Column('high', DECIMAL(30, 10), comment='最高价')
    low = Column('low', DECIMAL(30, 10), comment='最低价')
    close = Column('close', DECIMAL(30, 10), comment='收盘价')
    pre_close = Column('pre_close', DECIMAL(30, 10), comment='上一个交易日收盘价')
    change = Column('change', DECIMAL(30, 10), comment='涨跌额')
    pct_chg = Column('pct_chg', DECIMAL(30, 10), comment='涨跌幅, 未复权')
    vol = Column('vol', DECIMAL(30, 10), comment='成交量 手')
    amount = Column('amount', DECIMAL(30, 10), comment='成交额 千')


def create(engine):
    Base.metadata.create_all(engine)
