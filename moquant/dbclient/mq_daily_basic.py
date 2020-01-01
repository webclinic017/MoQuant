from sqlalchemy import Column, String, DECIMAL, Boolean, Index

from moquant.dbclient.base import Base


class MqDailyBasic(Base):
    __tablename__ = 'mq_daily_basic'
    __table_args__ = (
        Index('date_dpeg', 'date', 'dprofit_peg'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    ts_code = Column('ts_code', String(10), primary_key=True, comment='TS股票代码')
    share_name = Column('share_name', String(20), comment='股票名称')
    date = Column('date', String(10), primary_key=True, comment='日期')
    is_trade_day = Column('is_trade_day', Boolean, comment='是否交易日')
    total_share = Column('total_share', DECIMAL(30, 10), comment='期末总股本')
    close = Column('close', DECIMAL(30, 10), comment='当日收盘价')
    market_value = Column('market_value', DECIMAL(30, 10), comment='市值')
    pb = Column('pb', DECIMAL(30, 10), comment='PB')
    dprofit_period = Column('dprofit_period', String(10), comment='归母扣非净利润所属报告期 yyyyMMdd')
    dprofit_eps = Column('dprofit_eps', DECIMAL(30, 10), comment='归母扣非净利润PEPS')
    quarter_dprofit_yoy = Column('quarter_dprofit_yoy', DECIMAL(30, 10), comment='归母扣非净利润增速-单季')
    dprofit_pe = Column('dprofit_pe', DECIMAL(30, 10), comment='归母扣非净利润PE')
    dprofit_peg = Column('dprofit_peg', DECIMAL(30, 10), comment='归母扣非净利润PEG')
    grow_score = Column('grow_score', DECIMAL(30, 10), comment='成长股评分')
    dividend_yields = Column('dividend_yields', DECIMAL(30, 10), comment='股息率')
    val_score = Column('val_score', DECIMAL(30, 10), comment='价值股评分')
