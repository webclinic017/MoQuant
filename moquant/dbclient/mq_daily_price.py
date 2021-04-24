"""
每日价格相关，主要处理前复权问题
只有交易日
停牌日也有记录，但各数字为空
"""

from sqlalchemy import Column, String, DECIMAL, Index, BIGINT, INT

from moquant.dbclient.base import Base


class MqDailyPrice(Base):
    __tablename__ = 'mq_daily_price'
    __table_args__ = (
        Index('code_date', 'ts_code', 'div_date', 'trade_date'),
        Index('date', 'div_date', 'trade_date'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    id = Column('id', BIGINT, primary_key=True, comment='id', autoincrement=True)
    ts_code = Column('ts_code', String(10), comment='ts代码')
    div_date = Column('div_date', String(10), comment='上次除权日期')
    latest_adj = Column('latest_adj', DECIMAL(30, 10), comment='最新复权因子')
    trade_date = Column('trade_date', String(10), comment='交易日期')
    is_trade = Column('is_trade', INT, comment='是否可交易')

    adj = Column('adj', DECIMAL(30, 10), comment='交易日期的复权因子')
    open = Column('open', DECIMAL(30, 10), comment='开盘价')
    high = Column('high', DECIMAL(30, 10), comment='最高价')
    low = Column('low', DECIMAL(30, 10), comment='最低价')
    close = Column('close', DECIMAL(30, 10), comment='收盘价')
    up_limit = Column('up_limit', DECIMAL(30, 10), comment='涨停价')
    down_limit = Column('down_limit', DECIMAL(30, 10), comment='跌停价')

    open_qfq = Column('open_qfq', DECIMAL(30, 10), comment='开盘价-前复权')
    high_qfq = Column('high_qfq', DECIMAL(30, 10), comment='最高价-前复权')
    low_qfq = Column('low_qfq', DECIMAL(30, 10), comment='最低价-前复权')
    close_qfq = Column('close_qfq', DECIMAL(30, 10), comment='收盘价-前复权')
    up_limit_qfq = Column('up_limit_qfq', DECIMAL(30, 10), comment='涨停价-前复权')
    down_limit_qfq = Column('down_limit_qfq', DECIMAL(30, 10), comment='跌停价-前复权')
    pre_close_qfq = Column('pre_close_qfq', DECIMAL(30, 10), comment='上一个交易日收盘价-前复权')
