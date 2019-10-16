"""
计算逻辑备忘
1. 对于调整：年中财报有对去年进行调整的，计算ltm时在去年Q4上加上调整值
"""
from sqlalchemy import Column, String, DECIMAL, Boolean, Index

from moquant.dbclient.base import Base


class MqQuarterBasic(Base):
    __tablename__ = 'mq_quarter_basic'
    __table_args__ = (
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    ts_code = Column('ts_code', String(10), primary_key=True, comment='TS股票代码')
    share_name = Column('share_name', String(20), comment='股票名称')
    update_date = Column('update_date', String(10), primary_key=True, comment='更新日期，财报、预报、快报、调整发布日期')
    report_period = Column('report_period', String(10), primary_key=True, comment='最近一个已披露财报报告期 yyyyMMdd')
    forecast_period = Column('forecast_period', String(10), primary_key=True, comment='最近一个已披露预报、快报报告期 yyyyMMdd')
    revenue_period = Column('revenue_period', String(10), comment='营业收入所属报告期 yyyyMMdd')
    revenue = Column('revenue', DECIMAL(30, 10), comment='累计营业收入')
    revenue_ly = Column('revenue_ly', DECIMAL(30, 10), comment='去年累计营业收入')
    revenue_yoy = Column('revenue_yoy', DECIMAL(30, 10), comment='累计营业收入增速-同比')
    quarter_revenue = Column('quarter_revenue', DECIMAL(30, 10), comment='单季营业收入')
    quarter_revenue_ly = Column('quarter_revenue_ly', DECIMAL(30, 10), comment='去年同季营业收入')
    quarter_revenue_yoy = Column('quarter_revenue_yoy', DECIMAL(30, 10), comment='单季营业收入增速-同比')
    revenue_ltm = Column('revenue_ltm', DECIMAL(30, 10), comment='营业收入-LTM')
    nprofit_period = Column('nprofit_period', String(10), comment='归母净利润所属报告期 yyyyMMdd')
    nprofit = Column('nprofit', DECIMAL(30, 10), comment='累计归母净利润')
    nprofit_ly = Column('nprofit_ly', DECIMAL(30, 10), comment='去年累计归母净利润')
    nprofit_yoy = Column('nprofit_yoy', DECIMAL(30, 10), comment='累计归母净利润增速-同比')
    quarter_nprofit = Column('quarter_nprofit', DECIMAL(30, 10), comment='单季归母净利润')
    quarter_nprofit_ly = Column('quarter_nprofit_ly', DECIMAL(30, 10), comment='去年同季归母净利润')
    quarter_nprofit_yoy = Column('quarter_nprofit_yoy', DECIMAL(30, 10), comment='单季归母净利润增速-同比')
    nprofit_ltm = Column('nprofit_ltm', DECIMAL(30, 10), comment='LTM归母净利润')
    dprofit_period = Column('dprofit_period', String(10), comment='归母扣非净利润所属报告期 yyyyMMdd')
    dprofit = Column('dprofit', DECIMAL(30, 10), comment='累计归母扣非净利润')
    dprofit_ly = Column('dprofit_ly', DECIMAL(30, 10), comment='去年累计归母扣非净利润')
    dprofit_yoy = Column('dprofit_yoy', DECIMAL(30, 10), comment='累计归母扣非净利润增速-同比')
    quarter_dprofit = Column('quarter_dprofit', DECIMAL(30, 10), comment='单季归母扣非净利润')
    quarter_dprofit_ly = Column('quarter_dprofit_ly', DECIMAL(30, 10), comment='去年同季归母扣非净利润')
    quarter_dprofit_yoy = Column('quarter_dprofit_yoy', DECIMAL(30, 10), comment='单季归母扣非净利润增速-同比')
    dprofit_ltm = Column('dprofit_ltm', DECIMAL(30, 10), comment='LTM归母扣非净利润')
    nassets = Column('nassets', DECIMAL(30, 10), comment='归母净资产')
