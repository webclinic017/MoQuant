from sqlalchemy import Column, String, Boolean, BIGINT, Index

from moquant.dbclient.base import Base


class MqSharePool(Base):
    __tablename__ = 'mq_share_pool'
    __table_args__ = (
        Index('date_type', 'dt', 'strategy'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    id = Column('id', BIGINT, primary_key=True, comment='id', autoincrement=True)
    dt = Column('dt', String(10), comment='日期')
    strategy = Column('strategy', String(20), comment='策略类型')
    ts_code = Column('ts_code', String(20), comment='股票编码')
