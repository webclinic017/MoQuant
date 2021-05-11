"""
成长股打分 -1 为非成长股

剔除项:
PE > max_pe 或 PE < 0
单季利润为负 或 增速低于 min_yoy
净利增速基数 < min_dprofit
LTM净利为负 or 单季净利占LTM < min_dprofit_percent
PEG > max_peg

打分项:
PEG
"""

from decimal import Decimal

from moquant.constants import mq_daily_metric_enum, mq_quarter_metric_enum
from moquant.dbclient.mq_daily_metric import MqDailyMetric
from moquant.log import get_logger
from moquant.scripts import calculate
from moquant.service import mq_daily_store, mq_quarter_store
from moquant.utils import decimal_utils, date_utils
from moquant.utils.decimal_utils import valid_score

log = get_logger(__name__)

max_pe = Decimal(50)
max_peg = Decimal(0.2)
min_yoy = Decimal(0.5)
zero = Decimal(0)
min_dprofit = Decimal(1000 * 10000)
min_dprofit_percent = Decimal(0.15)


def cal(daily_store: mq_daily_store.MqDailyStore,
        quarter_store: mq_quarter_store.MqQuarterStore,
        ts_code: str, update_date: str) -> MqDailyMetric:
    score = 0
    peg = 0
    report_type = 0
    period = '00000000'
    pe: MqDailyMetric = daily_store.find_date_exact(ts_code, mq_daily_metric_enum.pe.name, update_date)
    dprofit_quarter = quarter_store.find_latest(ts_code, mq_quarter_metric_enum.dprofit_quarter.name, update_date)
    dprofit_quarter_ly = quarter_store.find_period_latest(
        ts_code, mq_quarter_metric_enum.dprofit_quarter.name,
        period=date_utils.period_delta(dprofit_quarter.period, -1),
        update_date=update_date) if dprofit_quarter is not None else None
    dprofit_ltm = quarter_store.find_latest(ts_code, mq_quarter_metric_enum.dprofit_ltm.name, update_date)

    if pe is None or dprofit_quarter is None or dprofit_quarter_ly is None or dprofit_ltm is None:
        score = -1
    elif calculate.gt(pe, max_pe, field='value') or calculate.lt(pe, zero, field='value'):
        score = -1
    elif calculate.lt(dprofit_quarter, zero, field='value') or calculate.lt(dprofit_quarter, min_yoy, field='yoy'):
        score = -1
    elif calculate.lt(dprofit_quarter_ly, min_dprofit, field='value'):
        score = -1
    elif calculate.lt(dprofit_ltm, zero, field='value') or \
            calculate.lt(decimal_utils.div(dprofit_quarter.value, dprofit_ltm.value), min_dprofit_percent):
        score = -1
    else:
        peg = decimal_utils.div(decimal_utils.div(pe.value, dprofit_quarter.yoy), 100)
        report_type = pe.report_type | dprofit_quarter.report_type
        period = max(pe.period, dprofit_quarter.period)
        if peg > max_peg:
            score = -1
        else:
            score = (1 - peg / max_peg) * 100

    peg_metric = MqDailyMetric(ts_code=ts_code, report_type=report_type,
                               period=period, update_date=update_date,
                               name=mq_daily_metric_enum.peg.name,
                               value=peg)
    grow_score_metric = MqDailyMetric(ts_code=ts_code, report_type=report_type,
                                      period=period, update_date=update_date,
                                      name=mq_daily_metric_enum.grow_score.name,
                                      value=valid_score(score))

    return [peg_metric, grow_score_metric]
