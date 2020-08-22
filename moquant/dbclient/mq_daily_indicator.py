from sqlalchemy import Column, String, DECIMAL, INT, Index

from moquant.dbclient.base import Base


class MqDailyIndicator(Base):
    __tablename__ = 'mq_daily_indicator'
    __table_args__ = (
        Index('score_list', 'name', 'update_date'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    ts_code = Column('ts_code', String(10), primary_key=True, comment='TS股票代码')
    update_date = Column('update_date', String(10), primary_key=True, comment='更新日期')
    period = Column('period', String(10), comment='报告期 yyyyMMdd')
    report_type = Column('report_type', INT, comment='指标类型 财报/预报/快报/预测/根据人工去预测/人工')
    name = Column('name', String(50), primary_key=True, comment='指标名称')
    value = Column('value', DECIMAL(30, 10), comment='指标值')

    def __gt__(self, other):
        return self.update_date > other.update_date

    def __ge__(self, other):
        return self > other or self == other

    def __eq__(self, other):
        return self.update_date == other.update_date

    def __le__(self, other):
        return self < other or self == other

    def __lt__(self, other):
        return self.update_date < other.update_date
