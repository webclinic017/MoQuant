from sqlalchemy import Column, String, DECIMAL, Boolean, Index, INT

from moquant.dbclient.base import Base


class MqQuarterIndex(Base):
    __tablename__ = 'mq_quarter_basic'
    __table_args__ = (
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    ts_code = Column('ts_code', String(10), primary_key=True, comment='TS股票代码')
    share_name = Column('share_name', String(20), comment='股票名称')
    update_date = Column('update_date', String(10), primary_key=True, comment='更新日期')
    period = Column('period', String(10), primary_key=True, comment='报告期 yyyyMMdd')
    index_type = Column('index_type', INT, comment='指标类型 财报/预报/快报/预测/人工')
    index_name = Column('index_name', String(20), primary_key=True, comment='指标名称')
    index_value = Column('index_value', DECIMAL(30, 10), comment='指标值')
