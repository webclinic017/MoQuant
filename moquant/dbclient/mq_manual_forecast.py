from sqlalchemy import Column, String, DECIMAL, Boolean, Index, BIGINT, INT

from moquant.dbclient.base import Base


class MqManualForecast(Base):
    __tablename__ = 'mq_manual_forecast'
    __table_args__ = (
        Index('code', 'ts_code'),
        Index('type', 'forecast_type'),
        Index('period', 'end_date'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    id = Column('id', BIGINT, primary_key=True, comment='id', autoincrement=True)
    ts_code = Column('ts_code', String(10), comment='TS股票代码')
    forecast_type = Column('forecast_type', INT, comment='预测报表类型 0-预报 1-快报')
    end_date = Column('end_date', String(10), comment='报告期')
    revenue = Column('revenue', DECIMAL(30, 10), comment='累计营业收入')
    nprofit = Column('nprofit', DECIMAL(30, 10), comment='累计归母净利润')
    dprofit = Column('dprofit', DECIMAL(30, 10), comment='累计归母扣非净利润')
