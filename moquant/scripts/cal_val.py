from decimal import Decimal

from moquant.dbclient.mq_daily_basic import MqDailyBasic
from moquant.dbclient.mq_quarter_basic import MqQuarterBasic
from moquant.log import get_logger
from moquant.utils.date_utils import get_quarter_num, period_delta

log = get_logger(__name__)


def earn_and_dividend_in_year(quarter_dict: dict, report_period: str, year: int) -> bool:
    quarter_num = get_quarter_num(report_period)
    period = report_period if quarter_num == 4 else period_delta(report_period, -quarter_num)
    period = period_delta(period, 4)
    for i in range(year):
        period = period_delta(period, -4)
        if period not in quarter_dict:
            continue
        quarter: MqQuarterBasic = quarter_dict[period]
        if quarter.dprofit_ltm is None or quarter.dprofit_ltm <= 0:
            return False
        if quarter.dividend_ltm is None or quarter.dividend_ltm <= 0:
            return False
    return True


def earn_in_period(quarter_dict: dict, report_period: str, quarter_num: int) -> bool:
    period = period_delta(report_period, 1)
    for i in range(quarter_num):
        period = period_delta(period, -1)
        if period not in quarter_dict:
            continue
        quarter: MqQuarterBasic = quarter_dict[period]
        if quarter.dprofit is None or quarter.dprofit <= 0:
            return False
    return True


def history_profit_yoy_score(quarter_dict: dict, report_period: str, year: int) -> bool:
    quarter_num = get_quarter_num(report_period)
    period = report_period if quarter_num == 4 else period_delta(report_period, -quarter_num)
    period = period_delta(period, 4)
    yoy_list = []
    for i in range(year):
        period = period_delta(period, -4)
        if period not in quarter_dict:
            continue
        quarter: MqQuarterBasic = quarter_dict[period]
        yoy_list.append(0 if quarter.dprofit_yoy is None else quarter.dprofit_yoy)

    result = 0
    score_per_one = 100 / year
    for yoy in yoy_list:
        if yoy > 0.1:
            result += score_per_one
        elif yoy <= 0:
            result -= score_per_one / 2
    return max(result, 0)


def history_dividend_yoy_score(quarter_dict: dict, report_period: str, year: int) -> bool:
    quarter_num = get_quarter_num(report_period)
    period = report_period if quarter_num == 4 else period_delta(report_period, -quarter_num)
    period = period_delta(period, 4)
    yoy_list = []
    for i in range(year):
        period = period_delta(period, -4)
        if period not in quarter_dict:
            continue
        quarter: MqQuarterBasic = quarter_dict[period]
        yoy_list.append(0 if quarter.dividend_ltm_yoy is None else quarter.dividend_ltm_yoy)

    result = 0
    score_per_one = 100 / year
    for yoy in yoy_list:
        if yoy > 0:
            result += score_per_one
        elif yoy < 0:
            result -= score_per_one / 2
    return max(result, 0)


def cal_val_score(daily: MqDailyBasic, quarter: MqQuarterBasic, quarter_dict: dict,
                  max_pe: Decimal = Decimal(15), max_pb: Decimal = Decimal(3), max_pepb: Decimal = Decimal(25)):
    score = 0
    if quarter.receive_risk > 0.5 or \
            quarter.liquidity_risk >= 0.6 or \
            quarter.intangible_risk > 0.25 or \
            not earn_and_dividend_in_year(quarter_dict, quarter.report_period, 5) or \
            not earn_in_period(quarter_dict, quarter.report_period, 4) or \
            (quarter.quarter_revenue_yoy is None or quarter.quarter_revenue_yoy < -0.15) or \
            (quarter.quarter_dprofit_yoy is None or quarter.quarter_dprofit_yoy < -0.15):
        score = -1

    if score != -1:
        dividend_score = daily.dividend_yields * 10  # / 0.1 * 100
        pe_score = max((1 - daily.dprofit_pe / max_pe) * 100, 0)
        pb_score = max((1 - daily.pb / max_pb) * 100, 0)
        pepb_score = max((1 - daily.dprofit_pe * daily.pb / max_pepb) * 100, 0)
        grow_score = history_profit_yoy_score(quarter_dict, quarter.report_period, 5)

        dividend_yoy_score = history_dividend_yoy_score(quarter_dict, quarter.report_period, 5)

        score = dividend_score * 0.3 + dividend_yoy_score * 0.2 + \
                (pe_score + pb_score + pepb_score) * 0.1 + grow_score * 0.2

    return max(score, 0)
