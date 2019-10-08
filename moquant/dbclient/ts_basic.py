""" Declaration of table `ts_basic` """

from sqlalchemy import Column, String, BIGINT, Index

from moquant.dbclient.base import Base


class TsBasic(Base):
    __tablename__ = 'ts_basic'
    __table_args__ = (
        Index('code', 'ts_code'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    id = Column('id', BIGINT, primary_key=True, comment='id', autoincrement=True)
    ts_code = Column('ts_code', String(10), comment='ts代码')
    symbol = Column('symbol', String(20), comment='股票代码')
    name = Column('name', String(20), comment='股票名称')
    area = Column('area', String(20), comment='所在区域')
    industry = Column('industry', String(20), comment='所属行业')
    fullname = Column('fullname', String(100), comment='股票全称')
    enname = Column('enname', String(100), comment='英文全称')
    market = Column('market', String(20), comment='市场类型（主板/中小板/创业板）')
    exchange = Column('exchange', String(20), comment='交易所代码')
    curr_type = Column('curr_type', String(20), comment='交易货币')
    list_status = Column('list_status', String(10), comment='上市状态: L上市 D退市 P暂停上市')
    list_date = Column('list_date', String(10), comment='上市日期')
    delist_date = Column('delist_date', String(10), comment='退市日期')
    is_hs = Column('is_hs', String(10), comment='是否沪深港通标的，N否 H沪股通 S深股通')


def create(engine):
    Base.metadata.create_all(engine)
