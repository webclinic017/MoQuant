from sqlalchemy import Column, String, DECIMAL, Boolean, Index, BIGINT, INT, Float

from moquant.dbclient.base import Base


class MqDcfConfig(Base):
    __tablename__ = 'mq_dcf_config'
    __table_args__ = (
        Index('code_name_time', 'ts_code', 'name', 'update_date'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    id = Column('id', BIGINT, primary_key=True, comment='id', autoincrement=True)
    ts_code = Column('ts_code', String(10), comment='TS股票代码')
    year = Column('year', INT, comment='年份')
    name = Column('name', String(20), comment='配置名称')
    value = Column('value', Float, comment='配置值')
    update_date = Column('update_date', String(10), comment='更新时间')
