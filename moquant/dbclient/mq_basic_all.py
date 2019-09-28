from sqlalchemy import Column, String, DECIMAL

from moquant.dbclient.base import Base


class MqStockBasicAll(Base):
    __tablename__ = 'mq_basic_all'
    __table_args__ = (
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    ts_code = Column('ts_code', String(10), primary_key=True, comment='TS股票代码')
    date = Column('date', String(10), primary_key=True, comment='日期')
    report_season = Column('report_season', String(10), comment='最近一个已披露财报报告期 yyyyMMdd')
    forecast_season = Column('forecast_season', String(10), comment='最近一个已披露预报、快报报告期 yyyyMMdd')
    total_share = Column('total_share', DECIMAL(30, 10), comment='期末总股本')
    close = Column('close', DECIMAL(30, 10), comment='当日收盘价')
    market_value = Column('market_value', DECIMAL(30, 10), comment='市值')
    nprofit_ltm = Column('nprofit_ltm', DECIMAL(30, 10), comment='LTM归母净利润')
    nprofit_ltm_pe = Column('nprofit_ltm_pe', DECIMAL(30, 10), comment='LTM归母净利润PE')
    eps_ltm = Column('eps_ltm', DECIMAL(30, 10), comment='LTM的EPS')
    season_revenue = Column('revenue', DECIMAL(30, 10), comment='单季营业收入')
    season_revenue_ly = Column('season_revenue_ly', DECIMAL(30, 10), comment='去年同季营业收入')
    season_revenue_yoy = Column('season_revenue_yoy', DECIMAL(30, 10), comment='单季营业收入增速-同比')
    revenue_peg = Column('revenue_peg', DECIMAL(30, 10), comment='营业收入PEG')
    season_nprofit = Column('season_nprofit', DECIMAL(30, 10), comment='单季归母净利润')
    season_nprofit_ly = Column('season_nprofit_ly', DECIMAL(30, 10), comment='去年同季归母净利润')
    season_nprofit_yoy = Column('season_nprofit_yoy', DECIMAL(30, 10), comment='单季归母净利润增速-同比')
    nprofit_peg = Column('nprofit_peg', DECIMAL(30, 10), comment='LTM归母净利润PEG')
    nassets = Column('nassets', DECIMAL(30, 10), comment='归母净资产')
    pb = Column('pb', DECIMAL(30, 10), comment='PB')
