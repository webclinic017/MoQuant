from sqlalchemy import Column, String, DECIMAL, Boolean, Index, BIGINT

from moquant.dbclient.base import Base


class MqFetchLatestRecord(Base):
    __tablename__ = 'mq_fetch_latest_record'
    __table_args__ = (
        Index('date', 'ann_date'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    id = Column('id', BIGINT, primary_key=True, comment='id', autoincrement=True)
    fetch_type = Column('fetch_type', String(10), comment='请求类型')
    ts_code = Column('ts_code', String(10), comment='ts代码')
    ann_date = Column('ann_date', String(10), comment='公告日期')
    end_date = Column('end_date', String(10), comment='报告期')
