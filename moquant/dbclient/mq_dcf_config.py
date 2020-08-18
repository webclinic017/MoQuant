from sqlalchemy import Column, String, DECIMAL, Boolean, Index, BIGINT, INT, Float

from moquant.dbclient.base import Base


class MqDcfConfig(Base):
    __tablename__ = 'mq_dcf_config'
    __table_args__ = (
        Index('code_time', 'ts_code', 'update_date'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    id = Column('id', BIGINT, primary_key=True, comment='id', autoincrement=True)
    ts_code = Column('ts_code', String(10), comment='TS股票代码')
    from_year = Column('from_year', INT, comment='起始年份-包含')
    to_year = Column('to_year', INT, comment='终止年份-包含')
    name = Column('name', String(20), comment='配置名称')
    value = Column('value', Float, comment='配置值')
    update_date = Column('update_date', String(10), comment='更新时间')

    def __gt__(self, other):
        return self.year > other.year or \
               (self.year == other.year and self.update_date > other.update_date)

    def __ge__(self, other):
        return self > other or self == other

    def __eq__(self, other):
        return self.year == other.year and self.update_date == other.update_date

    def __le__(self, other):
        return self < other or self == other

    def __lt__(self, other):
        return self.year < other.year or \
               (self.year == other.year and self.update_date < other.update_date)