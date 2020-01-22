from sqlalchemy import Column, String, DECIMAL, Boolean, Index, BIGINT, INT

from moquant.dbclient.base import Base


class MqManualReport(Base):
    __tablename__ = 'mq_manual_report'
    __table_args__ = (
        Index('code', 'ts_code'),
        Index('type', 'report_type'),
        Index('date', 'ann_date'),
        Index('period', 'end_date'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    id = Column('id', BIGINT, primary_key=True, comment='id', autoincrement=True)
    ts_code = Column('ts_code', String(10), comment='TS股票代码')
    ann_date = Column('ann_date', String(10), comment='公共日期')
    report_type = Column('report_type', INT, comment='预测报表类型 0-预报 1-财报')
    end_date = Column('end_date', String(10), comment='报告期')
    revenue = Column('revenue', DECIMAL(30, 10), comment='累计营业收入')
    revenue_ly = Column('revenue_ly', DECIMAL(30, 10), comment='累计营业收入-去年同期')
    nprofit = Column('nprofit', DECIMAL(30, 10), comment='累计归母净利润')
    nprofit_ly = Column('nprofit_ly', DECIMAL(30, 10), comment='累计归母净利润-去年同期')
    dprofit = Column('dprofit', DECIMAL(30, 10), comment='累计归母扣非净利润')
    dprofit_ly = Column('dprofit_ly', DECIMAL(30, 10), comment='累计归母扣非净利润-去年同期')
    changed_reason = Column('changed_reason', String(1000), comment='业绩变动原因')
    manual_adjust_reason = Column('manual_adjust_reason', String(1000), comment='人工调整原因')

