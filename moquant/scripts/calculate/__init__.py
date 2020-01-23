from moquant.log import get_logger
from moquant.scripts.calculate import cal_mq_quarter, cal_mq_forecast, cal_message
from moquant.scripts.calculate import cal_mq_daily

log = get_logger(__name__)


def run(ts_code):
    cal_mq_forecast.calculate_by_code(ts_code=ts_code)
    cal_mq_quarter.calculate_by_code(ts_code=ts_code)
    cal_mq_daily.calculate_by_code(ts_code=ts_code)
    cal_message.calculate_by_code(ts_code=ts_code)


def recalculate(ts_code: str):
    if ts_code is None:
        log.error('None ts_code to recalculate')
        return
    cal_mq_forecast.recalculate_by_code(ts_code=ts_code)
    cal_mq_quarter.recalculate_by_code(ts_code=ts_code)
    cal_mq_daily.recalculate_by_code(ts_code=ts_code)
    cal_message.recalculate_by_code(ts_code=ts_code)
