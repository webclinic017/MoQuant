from sqlalchemy import Column, String, DECIMAL, Boolean, Index, INT

from moquant.dbclient.base import Base
from moquant.utils.date_utils import *
from moquant.utils.decimal_utils import *


class MqQuarterIndex(Base):
    __tablename__ = 'mq_quarter_indicator'
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


def cal_quarter(i1: MqQuarterIndex, i2: MqQuarterIndex) -> MqQuarterIndex:
    if i1 is not None and get_quarter_num(i1.period) == 1:
        return MqQuarterIndex(ts_code=i1.ts_code, report_type=i1.report_type,
                              period=i1.period, update_date=i1.update_date,
                              name=i1.name + '_quarter', value=i1.value)
    elif i1 is None or i2 is None:
        return None
    return MqQuarterIndex(ts_code=i1.ts_code, report_type=i1.report_type | i2.report_type,
                          period=i1.period, update_date=i1.update_date,
                          name=i1.name + '_quarter', value=sub(i1.value, i2.value))


def cal_ltm(i1: MqQuarterIndex, lyy: MqQuarterIndex, ly: MqQuarterIndex) -> MqQuarterIndex:
    if i1 is not None and get_quarter_num(i1.period) == 4:
        return MqQuarterIndex(ts_code=i1.ts_code, report_type=i1.report_type,
                              period=i1.period, update_date=i1.update_date,
                              name=i1.name + '_ltm', value=i1.value)
    elif i1 is None or lyy is None or ly is None:
        return None
    else:
        return MqQuarterIndex(ts_code=i1.ts_code, report_type=i1.report_type & lyy.report_type | ly.report_type,
                              period=i1.period, update_date=i1.update_date,
                              name=i1.name + '_ltm', value=add(i1.value, sub(lyy.value, ly.value)))


def cal_ltm_avg(i1: MqQuarterIndex, i2: MqQuarterIndex, i3: MqQuarterIndex, i4: MqQuarterIndex) -> MqQuarterIndex:
    arr = [i1, i2, i3, i4]
    val = []
    avg = None
    report_type = 0
    for i in arr:
        if i is None:
            continue
        else:
            val.append(i.value)
            report_type = report_type | i.report_type
            if avg is None:
                avg = MqQuarterIndex(ts_code=i.ts_code, period=i.period, update_date=i.update_date,
                                     name=i.name + '_ltm_avg')
    if avg is not None:
        avg.value = avg_in_exists(val)
        avg.report_type = report_type
    return avg


def dividend(i1: MqQuarterIndex, i2: MqQuarterIndex, name: str) -> MqQuarterIndex:
    if i1 is None or i2 is None:
        return None
    return MqQuarterIndex(ts_code=i1.ts_code, report_type=i1.report_type | i2.report_type,
                          period=i1.period, update_date=i1.update_date,
                          name=name, value=div(i1.value, i2.value))


def add_up(name: str, arr: list) -> MqQuarterIndex:
    report_type = 0
    sum = None
    for i in arr:  # type: MqQuarterIndex
        if i is not None:
            if sum is None:
                sum = MqQuarterIndex(ts_code=i.ts_code, period=i.period, update_date=i.update_date,
                                     name=name)
            report_type = report_type | i.report_type
            sum.value = add(sum.value, i.value)
    sum.report_type = report_type
    return sum


def sub_from(name: str, arr: list) -> MqQuarterIndex:
    report_type = 0
    sum = None
    for index, i in enumerate(arr):  # type: MqQuarterIndex
        if i is not None:
            if sum is None:
                sum = MqQuarterIndex(ts_code=i.ts_code, period=i.period, update_date=i.update_date,
                                     name=name)
            report_type = report_type | i.report_type
            if index == 0:
                sum.value = add(sum.value, i.value)
            else:
                sum.value = sub(sum.value, i.value)
    sum.report_type = report_type
    return sum
