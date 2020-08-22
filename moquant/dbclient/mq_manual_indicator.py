from sqlalchemy import Column, String, DECIMAL, INT, Index, BIGINT

from moquant.dbclient.base import Base


class MqManualIndicator(Base):
    __tablename__ = 'mq_manual_indicator'
    __table_args__ = (
        Index('unique_indicator', 'ts_code', 'update_date', 'period', 'name', unique=True),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    id = Column('id', BIGINT, primary_key=True, comment='id', autoincrement=True)
    ts_code = Column('ts_code', String(10), comment='TS股票代码')
    update_date = Column('update_date', String(10), comment='更新日期')
    period = Column('period', String(10), comment='报告期 yyyyMMdd')
    report_type = Column('report_type', INT, comment='指标类型 财报/预报/快报/预测/根据人工去预测/人工')
    name = Column('name', String(50), comment='指标名称')
    value = Column('value', DECIMAL(30, 10), comment='指标值')
