from sqlalchemy import Column, BIGINT, Index, String, DECIMAL

from moquant.dbclient.base import Base


class TsDividend(Base):
    __tablename__ = 'ts_dividend'
    __table_args__ = (
        Index('code', 'ts_code'),
        Index('record', 'record_date'),
        Index('ex', 'ex_date'),
        Index('pay', 'pay_date'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    id = Column('id', BIGINT, primary_key=True, comment='id', autoincrement=True)
    ts_code = Column('ts_code', String(10), comment='TS代码')
    end_date = Column('end_date', String(10), comment='分红年度')
    ann_date = Column('ann_date', String(10), comment='预案公告日')
    div_proc = Column('div_proc', String(10), comment='实施进度')
    stk_div = Column('stk_div', DECIMAL(30, 10), comment='每股送转')
    stk_bo_rate = Column('stk_bo_rate', DECIMAL(30, 10), comment='每股送股比例')
    stk_co_rate = Column('stk_co_rate', DECIMAL(30, 10), comment='每股转增比例')
    cash_div = Column('cash_div', DECIMAL(30, 10), comment='每股分红（税后）')
    cash_div_tax = Column('cash_div_tax', DECIMAL(30, 10), comment='每股分红（税前）')
    record_date = Column('record_date', String(10), comment='股权登记日')
    ex_date = Column('ex_date', String(10), comment='除权除息日')
    pay_date = Column('pay_date', String(10), comment='派息日')
    div_listdate = Column('div_listdate', String(10), comment='红股上市日')
    imp_ann_date = Column('imp_ann_date', String(10), comment='实施公告日')
    base_date = Column('base_date', String(10), comment='基准日')
    base_share = Column('base_share', DECIMAL(30, 10), comment='基准股本（万）')
