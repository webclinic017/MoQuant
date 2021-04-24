"""
每日交易数据
非交易日、停牌日无数据
上一个交易日收盘价会前复权
有上市至今数据
"""

from sqlalchemy import Column, String, DECIMAL, Index, BIGINT

from moquant.dbclient.base import Base


class TsDailyTradeInfo(Base):
    __tablename__ = 'ts_daily_trade_info'
    __table_args__ = (
        Index('code_date', 'ts_code', 'trade_date'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    id = Column('id', BIGINT, primary_key=True, comment='id', autoincrement=True)
    ts_code = Column('ts_code', String(10), comment='ts代码')
    trade_date = Column('trade_date', String(10), comment='交易日期')
    open = Column('open', DECIMAL(30, 10), comment='开盘价')
    high = Column('high', DECIMAL(30, 10), comment='最高价')
    low = Column('low', DECIMAL(30, 10), comment='最低价')
    close = Column('close', DECIMAL(30, 10), comment='收盘价')
    pre_close = Column('pre_close', DECIMAL(30, 10), comment='上一个交易日收盘价')
    change = Column('change', DECIMAL(30, 10), comment='涨跌额')
    pct_chg = Column('pct_chg', DECIMAL(30, 10), comment='涨跌幅, 未复权')
    vol = Column('vol', DECIMAL(30, 10), comment='成交量 手')
    amount = Column('amount', DECIMAL(30, 10), comment='成交额 千')
