"""
按价值股打分

剔除项
风险点 > 0
股息率 < min_dividend_yields

筛选项
连续5年盈利和分红
连续4季度单季盈利

打分项
pe, pb, pepb 各 10%
分红 30%
分红增长 20%
利润增长 20%
"""
from decimal import Decimal
from functools import partial

from moquant.constants import mq_quarter_metric_enum, mq_daily_metric_enum, mq_report_type
from moquant.dbclient.mq_daily_metric import MqDailyMetric
from moquant.log import get_logger
from moquant.scripts import calculate
from moquant.service import mq_daily_store, mq_quarter_store
from moquant.utils import decimal_utils
from moquant.utils.date_utils import get_quarter_num, period_delta

log = get_logger(__name__)

zero = Decimal(0)
min_dividend_yields = Decimal(0.03)
max_desc_yoy = Decimal(-0.15)
max_pe = Decimal(15)
max_pb = Decimal(3)
max_pepb = Decimal(25)


def earn_and_dividend_in_year(quarter_store: mq_quarter_store.MqQuarterStore,
                              ts_code: str, report_period: str, update_date: str,
                              year: int) -> bool:
    quarter_num = get_quarter_num(report_period)
    period = report_period if quarter_num == 4 else period_delta(report_period, -quarter_num)
    period = period_delta(period, 4)
    for i in range(year):
        period = period_delta(period, -4)
        dprofit_ltm = quarter_store.find_period_latest(ts_code, mq_quarter_metric_enum.dprofit_ltm.name,
                                                       period, update_date)
        dividend_ltm = quarter_store.find_period_latest(ts_code, mq_quarter_metric_enum.dividend_ltm.name,
                                                        period, update_date)
        if calculate.lt(dprofit_ltm, zero, 'value', True):
            return False
        if calculate.lt(dividend_ltm, zero, 'value', True):
            return False
    return True


def earn_in_period(quarter_store: mq_quarter_store.MqQuarterStore,
                   ts_code: str, report_period: str, update_date: str,
                   quarter_num: int) -> bool:
    period = period_delta(report_period, 1)
    for i in range(quarter_num):
        period = period_delta(period, -1)
        dprofit_quarter = quarter_store.find_period_latest(ts_code, mq_quarter_metric_enum.dprofit_quarter.name,
                                                           period, update_date)
        if calculate.lt(dprofit_quarter, zero, 'value', True):
            return False
    return True


def history_profit_yoy_score(quarter_store: mq_quarter_store.MqQuarterStore,
                             ts_code: str, report_period: str, update_date: str,
                             year: int) -> bool:
    quarter_num = get_quarter_num(report_period)
    period = report_period if quarter_num == 4 else period_delta(report_period, -quarter_num)
    period = period_delta(period, 4)
    yoy_list = []
    for i in range(year):
        period = period_delta(period, -4)
        dprofit_ltm = quarter_store.find_period_latest(ts_code, mq_quarter_metric_enum.dprofit_ltm.name,
                                                       period, update_date)
        yoy_list.append(calculate.get_val(dprofit_ltm, 'yoy', zero))

    result = 0
    score_per_one = 100 / year
    for yoy in yoy_list:
        if yoy > 0.1:
            result += score_per_one
        elif yoy <= 0:
            result -= score_per_one / 2
    return decimal_utils.valid_score(result)


def history_dividend_yoy_score(quarter_store: mq_quarter_store.MqQuarterStore,
                               ts_code: str, report_period: str, update_date: str,
                               year: int) -> bool:
    quarter_num = get_quarter_num(report_period)
    period = report_period if quarter_num == 4 else period_delta(report_period, -quarter_num)
    period = period_delta(period, 4)
    yoy_list = []
    for i in range(year):
        period = period_delta(period, -4)
        dividend_ltm = quarter_store.find_period_latest(ts_code, mq_quarter_metric_enum.dividend_ltm.name,
                                                        period, update_date)
        yoy_list.append(calculate.get_val(dividend_ltm, 'yoy', zero))

    result = 0
    score_per_one = 100 / year
    for yoy in yoy_list:
        if yoy > 0:
            result += score_per_one
        elif yoy < 0:
            result -= score_per_one / 2
    return decimal_utils.valid_score(result)


def cal(daily_store: mq_daily_store.MqDailyStore,
        quarter_store: mq_quarter_store.MqQuarterStore,
        ts_code: str, update_date: str) -> MqDailyMetric:
    daily_find = partial(daily_store.find_date_exact, ts_code=ts_code, update_date=update_date)
    quarter_find = partial(quarter_store.find_latest, ts_code=ts_code, update_date=update_date)
    score = -1
    period = '00000000'
    dividend_yields = daily_find(name=mq_daily_metric_enum.dividend_yields.name)
    risk_point = quarter_find(name=mq_quarter_metric_enum.risk_point.name)
    revenue_quarter = quarter_find(name=mq_quarter_metric_enum.revenue_quarter.name)
    dprofit_quarter = quarter_find(name=mq_quarter_metric_enum.dprofit_quarter.name)

    if dividend_yields is None or \
            calculate.gt(risk_point, 0, 'value', True) or \
            calculate.lt(dividend_yields, 0.03, 'value', True) or \
            not earn_and_dividend_in_year(quarter_store, ts_code, dividend_yields.period, update_date, 5) or \
            not earn_in_period(quarter_store, ts_code, dividend_yields.period, update_date, 4) or \
            calculate.lt(revenue_quarter, max_desc_yoy, 'yoy', True) or \
            calculate.lt(revenue_quarter, dprofit_quarter, 'yoy', True):
        score = -1
    else:
        period = dividend_yields.period
        pe = daily_find(name=mq_daily_metric_enum.pe.name)
        pb = daily_find(name=mq_daily_metric_enum.pb.name)

        dividend_score = decimal_utils.mul(dividend_yields.value, Decimal(1000))  # * 100 / 10 * 100
        pe_score = decimal_utils.valid_score(
            (1 - decimal_utils.div(calculate.get_val(pe, 'value', max_pe), max_pe, err_default=0)) * 100)
        pb_score = decimal_utils.valid_score(
            (1 - decimal_utils.div(calculate.get_val(pb, 'value', max_pb), max_pb, err_default=0)) * 100)
        pepb_score = decimal_utils.valid_score(
            (1 - decimal_utils.div(
                decimal_utils.mul(calculate.get_val(pe, 'value', max_pe), calculate.get_val(pb, 'value', max_pb)),
                max_pepb)) * 100)

        profit_yoy_score = history_profit_yoy_score(quarter_store, ts_code, dividend_yields.period, update_date, 5)
        dividend_yoy_score = history_dividend_yoy_score(quarter_store, ts_code, dividend_yields.period, update_date, 5)

        if profit_yoy_score == 0 or dividend_yoy_score == 0:
            score = 0
        elif pe_score == 0 and pb_score == 0 and pepb_score == 0:
            score = 0
        else:
            score = decimal_utils.add(
                decimal_utils.mul(dividend_score, 0.3),
                decimal_utils.mul(dividend_yoy_score, 0.2),
                decimal_utils.mul((pe_score + pb_score + pepb_score), 0.1),
                decimal_utils.mul(profit_yoy_score, 0.2))

    val_score_metric = MqDailyMetric(ts_code=ts_code, report_type=mq_report_type.mq_predict,
                                     period=period, update_date=update_date,
                                     name=mq_daily_metric_enum.val_score.name,
                                     value=decimal_utils.valid_score(score))
    return [val_score_metric]
