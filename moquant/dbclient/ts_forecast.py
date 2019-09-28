
from sqlalchemy import Column, BIGINT, Index, String, DECIMAL

from moquant.dbclient.base import Base


class StockForecast(Base):
    __tablename__ = 'ts_forecast'
    __table_args__ = (
        Index('code_date', 'ts_code', 'ann_date'),
        Index('code_period', 'ts_code', 'end_date'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    id = Column('id', BIGINT, primary_key=True, comment='id', autoincrement=True)
    ts_code = Column('ts_code', String(10), comment='TS股票代码')
    ann_date = Column('ann_date', String(10), comment='公告日期')
    end_date = Column('end_date', String(10), comment='报告期')
    type = Column('type', String(10), comment='业绩预告类型(预增/预减/扭亏/首亏/续亏/续盈/略增/略减)')
    p_change_min = Column('p_change_min', DECIMAL(30, 10), comment='预告净利润变动幅度下限（%）')
    p_change_max = Column('p_change_max', DECIMAL(30, 10), comment='预告净利润变动幅度上限（%）')
    net_profit_min = Column('net_profit_min', DECIMAL(30, 10), comment='预告净利润下限（万元）')
    net_profit_max = Column('net_profit_max', DECIMAL(30, 10), comment='预告净利润上限（万元）')
    last_parent_net = Column('last_parent_net', DECIMAL(30, 10), comment='上年同期归属母公司净利润')
    first_ann_date = Column('first_ann_date', String(10), comment='首次公告日')
    summary = Column('summary', String(5000), comment='业绩预告摘要')
    change_reason = Column('change_reason', String(5000), comment='业绩变动原因')

