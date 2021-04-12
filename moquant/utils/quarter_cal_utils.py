from moquant.dbclient.mq_quarter_metric import MqQuarterMetric
from moquant.utils import date_utils, decimal_utils


def cal_quarter(name: str, i1: MqQuarterMetric, i2: MqQuarterMetric) -> MqQuarterMetric:
    if i1 is not None and date_utils.get_quarter_num(i1.period) == 1:
        return MqQuarterMetric(ts_code=i1.ts_code, report_type=i1.report_type,
                               period=i1.period, update_date=i1.update_date,
                               name=name, value=i1.value)
    elif i1 is None or i2 is None:
        return None
    return MqQuarterMetric(ts_code=i1.ts_code, report_type=i1.report_type | i2.report_type,
                           period=i1.period, update_date=i1.update_date,
                           name=name, value=decimal_utils.sub(i1.value, i2.value))


def cal_ltm_with_quarter(name: str, i1: MqQuarterMetric, i2: MqQuarterMetric, i3: MqQuarterMetric, i4) -> MqQuarterMetric:
    '''
    用4个单季去计算LTM
    '''
    if i1 is not None and date_utils.get_quarter_num(i1.period) == 4:
        return MqQuarterMetric(ts_code=i1.ts_code, report_type=i1.report_type,
                               period=i1.period, update_date=i1.update_date,
                               name=name, value=i1.value)
    elif i1 is None or i2 is None or i3 is None or i4 is None:
        return None
    else:
        return MqQuarterMetric(ts_code=i1.ts_code,
                               report_type=i1.report_type | i2.report_type | i3.report_type | i4.report_type,
                               period=i1.period, update_date=i1.update_date,
                               name=name, value=decimal_utils.add(i1.value, i2.value, i3.value, i4.value))


def cal_ltm_with_period(name: str, current: MqQuarterMetric, last_year_q4: MqQuarterMetric, last_year: MqQuarterMetric) -> MqQuarterMetric:
    '''
    用季度去计算LTM
    '''
    if current is None:
        return None

    if date_utils.get_quarter_num(current.period) == 4:
        return add_up(name, [current])
    elif last_year_q4 is None or last_year is None:
        return None
    else:
        return add_up(name, [current, sub_from('_', [last_year_q4, last_year])])


def cal_ltm_avg(name: str, i1: MqQuarterMetric, i2: MqQuarterMetric, i3: MqQuarterMetric,
                i4: MqQuarterMetric) -> MqQuarterMetric:
    if i1 is None:
        return None
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
                avg = MqQuarterMetric(ts_code=i.ts_code, period=i.period, update_date=i.update_date,
                                      name=name)
    if avg is not None:
        avg.value = decimal_utils.avg_in_exists(*val)
        avg.report_type = report_type
    return avg


def dividend(i1: MqQuarterMetric, i2: MqQuarterMetric, name: str) -> MqQuarterMetric:
    if i1 is None or i2 is None:
        return None
    return MqQuarterMetric(ts_code=i1.ts_code, report_type=i1.report_type | i2.report_type,
                           period=i1.period, update_date=i1.update_date,
                           name=name, value=decimal_utils.div(i1.value, i2.value))


def multiply(i1: MqQuarterMetric, i2: MqQuarterMetric, name: str) -> MqQuarterMetric:
    if i1 is None or i2 is None:
        return None
    return MqQuarterMetric(ts_code=i1.ts_code, report_type=i1.report_type | i2.report_type,
                           period=i1.period, update_date=i1.update_date,
                           name=name, value=decimal_utils.mul(i1.value, i2.value))


def add_up(name: str, arr: list) -> MqQuarterMetric:
    report_type = 0
    sum = None
    for i in arr:  # type: MqQuarterMetric
        if i is not None:
            if sum is None:
                sum = MqQuarterMetric(ts_code=i.ts_code, period=i.period, update_date=i.update_date,
                                      name=name)
            report_type = report_type | i.report_type
            sum.value = decimal_utils.add(sum.value, i.value)
    if sum is not None:
        sum.report_type = report_type
    return sum


def sub_from(name: str, arr: list) -> MqQuarterMetric:
    report_type = 0
    sum = None
    for index, i in enumerate(arr):  # type: MqQuarterMetric
        if i is not None:
            if sum is None:
                sum = MqQuarterMetric(ts_code=i.ts_code, period=i.period, update_date=i.update_date,
                                      name=name)
            report_type = report_type | i.report_type
            if index == 0:
                sum.value = decimal_utils.add(sum.value, i.value)
            else:
                sum.value = decimal_utils.sub(sum.value, i.value)
    if sum is not None:
        sum.report_type = report_type
    return sum
