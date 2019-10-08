from sqlalchemy import Column, String, DECIMAL, Boolean, Index

from moquant.dbclient.base import Base


class MqDailyBasic(Base):
    __tablename__ = 'mq_daily_basic'
    __table_args__ = (
        Index('date_npeg', 'date', 'nprofit_peg'),
        Index('date_dpeg', 'date', 'dprofit_peg'),
        Index('date_ng', 'date', 'season_nprofit_yoy'),
        Index('date_dg', 'date', 'season_dprofit_yoy'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    ts_code = Column('ts_code', String(10), primary_key=True, comment='TS股票代码')
    share_name = Column('share_name', String(20), comment='股票名称')
    date = Column('date', String(10), primary_key=True, comment='日期')
    report_season = Column('report_season', String(10), comment='最近一个已披露财报报告期 yyyyMMdd')
    forecast_season = Column('forecast_season', String(10), comment='最近一个已披露预报、快报报告期 yyyyMMdd')
    total_share = Column('total_share', DECIMAL(30, 10), comment='期末总股本')
    close = Column('close', DECIMAL(30, 10), comment='当日收盘价')
    market_value = Column('market_value', DECIMAL(30, 10), comment='市值')
    season_revenue = Column('season_revenue', DECIMAL(30, 10), comment='单季营业收入')
    season_revenue_ly = Column('season_revenue_ly', DECIMAL(30, 10), comment='去年同季营业收入')
    season_revenue_yoy = Column('season_revenue_yoy', DECIMAL(30, 10), comment='单季营业收入增速-同比')
    season_nprofit = Column('season_nprofit', DECIMAL(30, 10), comment='单季归母净利润')
    season_nprofit_ly = Column('season_nprofit_ly', DECIMAL(30, 10), comment='去年同季归母净利润')
    season_nprofit_yoy = Column('season_nprofit_yoy', DECIMAL(30, 10), comment='单季归母净利润增速-同比')
    nprofit_ltm = Column('nprofit_ltm', DECIMAL(30, 10), comment='LTM归母净利润')
    nprofit_eps = Column('nprofit_eps', DECIMAL(30, 10), comment='归母净利润PEPS')
    nprofit_pe = Column('nprofit_pe', DECIMAL(30, 10), comment='归母净利润PE')
    nprofit_peg = Column('nprofit_peg', DECIMAL(30, 10), comment='归母净利润PEG')
    season_dprofit = Column('season_dprofit', DECIMAL(30, 10), comment='单季归母扣非净利润')
    season_dprofit_ly = Column('season_dprofit_ly', DECIMAL(30, 10), comment='去年同季归母扣非净利润')
    season_dprofit_yoy = Column('season_dprofit_yoy', DECIMAL(30, 10), comment='单季归母扣非净利润增速-同比')
    dprofit_ltm = Column('dprofit_ltm', DECIMAL(30, 10), comment='LTM归母扣非净利润')
    dprofit_eps = Column('dprofit_eps', DECIMAL(30, 10), comment='归母扣非净利润PEPS')
    dprofit_pe = Column('dprofit_pe', DECIMAL(30, 10), comment='归母扣非净利润PE')
    dprofit_peg = Column('dprofit_peg', DECIMAL(30, 10), comment='归母扣非净利润PEG')
    nassets = Column('nassets', DECIMAL(30, 10), comment='归母净资产')
    pb = Column('pb', DECIMAL(30, 10), comment='PB')
    is_trade_day = Column('is_trade_day', Boolean, comment='是否交易日')
