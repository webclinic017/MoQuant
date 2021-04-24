from decimal import Decimal

from moquant.log import get_logger
from moquant.scripts.calculate import cal_mq_quarter, cal_message, cal_mq_daily_price
from moquant.scripts.calculate import cal_mq_daily
from moquant.utils import date_utils

log = get_logger(__name__)


def run(ts_code, to_date=date_utils.get_current_dt()):
    if ts_code is None:
        log.error('None ts_code to calculate')
        return
    cal_mq_quarter.calculate_by_code(ts_code=ts_code, to_date=to_date)
    cal_mq_daily.calculate_by_code(ts_code=ts_code, to_date=to_date)
    cal_mq_daily_price.calculate_by_code(ts_code=ts_code, to_date=to_date)
    cal_message.calculate_by_code(ts_code=ts_code, to_date=to_date)


def recalculate(ts_code: str, to_date=date_utils.get_current_dt(), from_date=None):
    if ts_code is None:
        log.error('None ts_code to recalculate')
        return
    if from_date is not None:
        remove_after_fetch(ts_code, from_date)
        run(ts_code, to_date)
    else:
        cal_mq_quarter.recalculate_by_code(ts_code=ts_code, to_date=to_date)
        cal_mq_daily.recalculate_by_code(ts_code=ts_code, to_date=to_date)
        cal_mq_daily_price.recalculate_by_code(ts_code=ts_code, to_date=to_date)
        cal_message.recalculate_by_code(ts_code=ts_code, to_date=to_date)


def gt(obj: object, target: object, field: str = None, none_ret: bool = False) -> bool:
    if obj is None:
        return none_ret
    value = getattr(obj, field) if field is not None else obj
    if value is None:
        return none_ret
    return value > target


def lt(obj: object, target: object, field: str = None, none_ret: bool = False) -> bool:
    if obj is None:
        return none_ret
    value = getattr(obj, field) if field is not None else obj
    if value is None:
        return none_ret
    return value < target


def get_val(obj: object, field: str = None, none_ret: Decimal = Decimal(0)) -> Decimal:
    if obj is None:
        return none_ret
    value = getattr(obj, field) if field is not None else obj
    if value is None:
        return none_ret
    return value


def remove_after_fetch(ts_code: str, from_date: str):
    cal_mq_quarter.remove_from_date(ts_code, from_date)
    cal_mq_daily.remove_from_date(ts_code, from_date)
    cal_mq_daily_price.remove_from_date(ts_code, from_date)
    cal_message.remove_from_date(ts_code, from_date)
