from sqlalchemy import Column, String, DECIMAL, Boolean, Index, BIGINT, INT

from moquant.dbclient.base import Base


class MqForecastAgg(Base):
    __tablename__ = 'mq_forecast_agg'
    __table_args__ = (
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    ts_code = Column('ts_code', String(10), primary_key=True, comment='TS股票代码')
    ann_date = Column('ann_date', String(10), primary_key=True, comment='公共日期')
    end_date = Column('end_date', String(10), primary_key=True, comment='报告期')
    forecast_type = Column('forecast_type', INT, comment='类型 1-预报 2-快报')
    revenue = Column('revenue', DECIMAL(30, 10), comment='累计营业收入')
    revenue_ly = Column('revenue_ly', DECIMAL(30, 10), comment='累计营业收入-去年同期')
    nprofit = Column('nprofit', DECIMAL(30, 10), comment='累计归母净利润')
    nprofit_ly = Column('nprofit_ly', DECIMAL(30, 10), comment='累计归母净利润-去年同期')
    dprofit = Column('dprofit', DECIMAL(30, 10), comment='累计归母扣非净利润')
    dprofit_ly = Column('dprofit_ly', DECIMAL(30, 10), comment='累计归母扣非净利润-去年同期')
    changed_reason = Column('changed_reason', String(5000), comment='业绩变动原因')
    manual_adjust_reason = Column('manual_adjust_reason', String(5000), comment='人工调整原因')
    from_manual = Column('from_manual', Boolean, server_default='0', comment='来自人工导入')
    one_time = Column('one_time', Boolean, server_default='0', comment='是否一次性的利润变动')



