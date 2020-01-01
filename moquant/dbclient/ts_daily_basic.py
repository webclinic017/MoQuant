""" Declaration of table `ts_daily_trade_info` """

from sqlalchemy import Column, String, DECIMAL, Index, BIGINT

from moquant.dbclient.base import Base


class TsDailyBasic(Base):
    __tablename__ = 'ts_daily_basic'
    __table_args__ = (
        Index('code_date', 'ts_code', 'trade_date'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    id = Column('id', BIGINT, primary_key=True, comment='id', autoincrement=True)
    ts_code = Column('ts_code', String(10), comment='TS股票代码')
    trade_date = Column('trade_date', String(10), comment='交易日期')
    close = Column('close', DECIMAL(30, 10), comment='当日收盘价')
    turnover_rate = Column('turnover_rate', DECIMAL(30, 10), comment='换手率（%）')
    turnover_rate_f = Column('turnover_rate_f', DECIMAL(30, 10), comment='换手率（自由流通股）')
    volume_ratio = Column('volume_ratio', DECIMAL(30, 10), comment='量比')
    pe = Column('pe', DECIMAL(30, 10), comment='市盈率（总市值/净利润）')
    pe_ttm = Column('pe_ttm', DECIMAL(30, 10), comment='市盈率（TTM）')
    pb = Column('pb', DECIMAL(30, 10), comment='市净率（总市值/净资产）')
    ps = Column('ps', DECIMAL(30, 10), comment='市销率')
    ps_ttm = Column('ps_ttm', DECIMAL(30, 10), comment='市销率（TTM）')
    dv_ratio = Column('dv_ratio', DECIMAL(30, 10), comment='股息率 （%）')
    dv_ttm = Column('dv_ttm', DECIMAL(30, 10), comment='股息率（TTM）（%）')
    total_share = Column('total_share', DECIMAL(30, 10), comment='总股本 （万股）')
    float_share = Column('float_share', DECIMAL(30, 10), comment='流通股本 （万股）')
    free_share = Column('free_share', DECIMAL(30, 10), comment='自由流通股本 （万）')
    total_mv = Column('total_mv', DECIMAL(30, 10), comment='总市值 （万元）')
    circ_mv = Column('circ_mv', DECIMAL(30, 10), comment='流通市值（万元）')


def create(engine):
    Base.metadata.create_all(engine)
