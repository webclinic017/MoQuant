""" Declaration of table `mq_stock_mark` """

from sqlalchemy import Column, String, Boolean, DECIMAL

from moquant.dbclient.base import Base


class MqStockMark(Base):
    __tablename__ = 'mq_stock_mark'
    __table_args__ = (
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    ts_code = Column('ts_code', String(10), primary_key=True, comment='ts代码')
    share_name = Column('share_name', String(20), comment='股票名称')
    last_fetch_date = Column('last_fetch_date', String(10), comment='最后处理日期')
    fetch_data = Column('fetch_data', Boolean, comment='是否拉取数据')
    last_daily_cal = Column('last_daily_cal', String(10), comment='最后计算日期')
    grow_score = Column('grow_score', DECIMAL(30, 10), comment='成长股评分')


def create(engine):
    Base.metadata.create_all(engine)
