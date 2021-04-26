from sqlalchemy import Column, String, DECIMAL, BIGINT, Index

from moquant.dbclient.base import Base


class TsTradeCal(Base):
    __tablename__ = 'ts_trade_cal'
    __table_args__ = (
        Index('exchange', 'exchange', 'cal_date'),
        Index('is_open', 'is_open'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    id = Column('id', BIGINT, primary_key=True, comment='id', autoincrement=True)
    exchange = Column('exchange', String(10), comment='交易所 SSE上交所 SZSE深交所')
    cal_date = Column('cal_date', String(10), comment='日历日期')
    is_open = Column('is_open', String(10), comment='是否交易 0休市 1交易')
    pretrade_date = Column('pretrade_date', String(10), comment='上一个交易日')
