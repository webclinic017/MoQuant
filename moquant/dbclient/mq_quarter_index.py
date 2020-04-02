from sqlalchemy import Column, String, DECIMAL, Boolean, Index, INT

from moquant.dbclient.base import Base


class MqQuarterIndex(Base):
    __tablename__ = 'mq_quarter_index'
    __table_args__ = (
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    ts_code = Column('ts_code', String(10), primary_key=True, comment='TS股票代码')
    share_name = Column('share_name', String(20), comment='股票名称')
    update_date = Column('update_date', String(10), primary_key=True, comment='更新日期')
    period = Column('period', String(10), primary_key=True, comment='报告期 yyyyMMdd')
    report_type = Column('report_type', INT, comment='指标类型 财报/预报/快报/预测/根据人工去预测/人工')
    name = Column('name', String(20), primary_key=True, comment='指标名称')
    value = Column('value', DECIMAL(30, 10), comment='指标值')
    yoy = Column('yoy', DECIMAL(30, 10), comment='同比')
    mom = Column('mom', DECIMAL(30, 10), comment='环比')

    def __gt__(self, other):
        return self.period > other.period or \
               (self.period == other.period and self.update_date > other.update_date)

    def __ge__(self, other):
        return self > other or self == other

    def __eq__(self, other):
        return self.period == other.period and self.update_date == other.update_date

    def __le__(self, other):
        return self < other or self == other

    def __lt__(self, other):
        return self.period < other.period or \
               (self.period == other.period and self.update_date < other.update_date)
