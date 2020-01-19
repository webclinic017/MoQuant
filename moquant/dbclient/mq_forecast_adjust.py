from sqlalchemy import Column, String, DECIMAL, Boolean, Index, BIGINT, INT

from moquant.dbclient.base import Base


class MqForecastAdjust(Base):
    __tablename__ = 'mq_forecast_adjust'
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
    dprofit = Column('dprofit', DECIMAL(30, 10), comment='累计归母扣非净利润')
    remark = Column('remark', String(100), comment='备注')
    one_time = Column('one_time', Boolean, server_default='0', comment='是否一次性的利润变动')
