import sys
import time
from decimal import Decimal
from functools import partial

from sqlalchemy.orm import Session

from moquant.constants import mq_calculate_start_date, mq_daily_indicator_enum, mq_report_type, \
    mq_quarter_indicator_enum
from moquant.dbclient import db_client
from moquant.dbclient.mq_daily_indicator import MqDailyIndicator
from moquant.dbclient.mq_quarter_indicator import MqQuarterIndicator
from moquant.dbclient.ts_basic import TsBasic
from moquant.dbclient.ts_daily_basic import TsDailyBasic
from moquant.log import get_logger
from moquant.scripts.calculate import cal_grow
from moquant.service import mq_quarter_store, mq_daily_store
from moquant.utils import decimal_utils, date_utils

log = get_logger(__name__)


def common_add(result_list: list, store: mq_daily_store.MqDailyStore, to_add: MqDailyIndicator):
    store.add(to_add)
    result_list.append(to_add)


def common_log_err(ts_code: str, update_date: str, name: str):
    log.error('Fail to cal %s of %s, date: %s' % (name, ts_code, update_date))


def add_nx(ts_code: str, report_type: int, period: str, update_date: str,
           name: str, value: Decimal,
           result_list: list, store: mq_daily_store.MqDailyStore):
    if value is None:
        return
    exist = store.find_date_exact(ts_code, name, period)
    if exist is not None:
        return
    to_add = MqDailyIndicator(ts_code=ts_code, report_type=(1 << report_type), period=period, update_date=update_date,
                              name=name, value=value)
    common_add(result_list, store, to_add)


def extract_from_daily_basic(result_list: list, store: mq_daily_store.MqDailyStore, daily: TsDailyBasic):
    call_add_nx = partial(
        add_nx, ts_code=daily.ts_code, period=daily.trade_date, update_date=daily.trade_date,
        report_type=mq_report_type.report, store=store, result_list=result_list
    )
    for i in mq_daily_indicator_enum.extract_from_daily_list:
        call_add_nx(name=i.name, value=getattr(daily, i.name))


def copy_basic_from_yesterday(result_list: list, store: mq_daily_store.MqDailyStore, ts_code, now_date):
    yesterday_date = date_utils.format_delta(now_date, -1)
    for i in mq_daily_indicator_enum.extract_from_daily_list:
        yesterday = store.find_date_exact(ts_code, i.name, yesterday_date)
        if yesterday is None:
            log.error('Cant find daily data of %s %s to copy for non-trade-day' % (ts_code, yesterday))
        else:
            to_add = MqDailyIndicator(ts_code=yesterday.ts_code, report_type=yesterday.report_type,
                                      period=yesterday.period, update_date=now_date,
                                      name=yesterday.name, value=yesterday.value)
            common_add(result_list, store, to_add)


# daily / quarter
def dq_dividend(call_add: partial, call_log: partial, i1: MqDailyIndicator, i2: MqQuarterIndicator, name: str):
    if i1 is None or i2 is None:
        call_log(name=name)
        return None
    else:
        to_add = MqDailyIndicator(ts_code=i1.ts_code, report_type=i1.report_type | i2.report_type,
                                  period=i2.period, update_date=i1.update_date,
                                  name=name, value=decimal_utils.div(i1.value, i2.value))
        call_add(to_add=to_add)
        return to_add


# quarter / daily
def qd_dividend(call_add: partial, call_log: partial, i1: MqQuarterIndicator, i2: MqDailyIndicator, name: str):
    if i1 is None or i2 is None:
        call_log(name=name)
        return None
    else:
        to_add = MqDailyIndicator(ts_code=i1.ts_code, report_type=i1.report_type | i2.report_type,
                                  period=i1.period, update_date=i2.update_date,
                                  name=name, value=decimal_utils.div(i1.value, i2.value))
        call_add(to_add=to_add)
        return to_add


def cal_pepb(result_list: list, daily_store: mq_daily_store.MqDailyStore,
             quarter_store: mq_quarter_store.MqQuarterStore,
             ts_code: str, update_date: str):
    call_add = partial(common_add, result_list=result_list, store=daily_store)
    call_log = partial(common_log_err, ts_code=ts_code, update_date=update_date)

    total_mv = daily_store.find_date_exact(ts_code, mq_daily_indicator_enum.total_mv.name, update_date)

    dprofit_ltm = quarter_store.find_latest(ts_code, mq_quarter_indicator_enum.dprofit_ltm.name, update_date)
    dq_dividend(call_add, call_log, total_mv, dprofit_ltm, mq_daily_indicator_enum.pe.name)

    nassets = quarter_store.find_latest(ts_code, mq_quarter_indicator_enum.nassets.name, update_date)
    dq_dividend(call_add, call_log, total_mv, nassets, mq_daily_indicator_enum.pb.name)


def cal_dividend(result_list: list, daily_store: mq_daily_store.MqDailyStore,
                 quarter_store: mq_quarter_store.MqQuarterStore,
                 ts_code: str, update_date: str):
    call_add = partial(common_add, result_list=result_list, store=daily_store)
    call_log = partial(common_log_err, ts_code=ts_code, update_date=update_date)

    dividend_ltm = quarter_store.find_latest(ts_code, mq_quarter_indicator_enum.dividend_ltm.name, update_date)
    total_mv = daily_store.find_date_exact(ts_code, mq_daily_indicator_enum.total_mv.name, update_date)
    qd_dividend(call_add, call_log, dividend_ltm, total_mv, mq_daily_indicator_enum.dividend_yields.name)


def cal_dcf(result_list: list, daily_store: mq_daily_store.MqDailyStore,
                 quarter_store: mq_quarter_store.MqQuarterStore,
                 ts_code: str, update_date: str):
    '''
        根据自由现金流估算市值
    '''
    call_add = partial(common_add, result_list=result_list, store=daily_store)
    call_log = partial(common_log_err, ts_code=ts_code, update_date=update_date)




def cal_score(result_list: list, daily_store: mq_daily_store.MqDailyStore,
              quarter_store: mq_quarter_store.MqQuarterStore,
              ts_code: str, update_date: str):
    call_add = partial(common_add, result_list=result_list, store=daily_store)

    grow_score = cal_grow.cal(daily_store, quarter_store, ts_code, update_date)
    call_add(to_add=grow_score)



def calculate_one(ts_code: str, share_name: str, to_date: str = date_utils.get_current_dt()):
    start_time = time.time()
    result_list = []
    session = db_client.get_session()
    last_mq_daily = session.query(MqDailyIndicator).filter(MqDailyIndicator.ts_code == ts_code) \
        .order_by(MqDailyIndicator.update_date.desc()).limit(1).all()

    from_date = mq_calculate_start_date
    if len(last_mq_daily) > 0:
        from_date = date_utils.format_delta(last_mq_daily[0].update_date, 1)
    else:
        ts_basic_arr = session.query(TsBasic).filter(TsBasic.ts_code == ts_code).all()
        if len(ts_basic_arr) > 0 and ts_basic_arr[0].list_date > from_date:
            from_date = ts_basic_arr[0].list_date

    # Get all daily basic from a date
    last_ts_daily = session.query(TsDailyBasic) \
        .filter(TsDailyBasic.ts_code == ts_code, TsDailyBasic.trade_date < from_date) \
        .order_by(TsDailyBasic.trade_date.desc()) \
        .limit(1) \
        .all()
    daily_start_date = last_ts_daily[0].trade_date if len(last_ts_daily) > 0 else from_date

    daily_arr = session.query(TsDailyBasic) \
        .filter(TsDailyBasic.ts_code == ts_code, TsDailyBasic.trade_date >= daily_start_date) \
        .order_by(TsDailyBasic.trade_date.asc()).all()
    if len(daily_arr) > 0 and daily_arr[0].trade_date > from_date:
        from_date = daily_arr[0].trade_date

    session.close()

    quarter_store = mq_quarter_store.init_quarter_store_by_date(ts_code, date_utils.format_delta(from_date, -360))
    daily_store = mq_daily_store.init_daily_store_by_date(ts_code, date_utils.format_delta(from_date, -360))

    prepare_time = time.time()
    log.info("Prepare data for %s: %s seconds" % (ts_code, prepare_time - start_time))

    while from_date <= to_date:
        is_trade_day: bool = (len(daily_arr) > 0 and daily_arr[0].trade_date == from_date)

        if is_trade_day:
            extract_from_daily_basic(result_list, daily_store, daily_arr.pop(0))
        else:
            copy_basic_from_yesterday(result_list, daily_store, ts_code, from_date)

        cal_pepb(result_list, daily_store, quarter_store, ts_code, from_date)
        cal_dividend(result_list, daily_store, quarter_store, ts_code, from_date)
        cal_dcf(result_list, daily_store, quarter_store, ts_code, from_date)
        cal_score(result_list, daily_store, quarter_store, ts_code, from_date)

        from_date = date_utils.format_delta(from_date, 1)

    calculate_time = time.time()
    log.info("Calculate mq_daily_indicator for %s: %s seconds" % (ts_code, calculate_time - prepare_time))
    return result_list


def calculate_and_insert(ts_code: str, share_name: str, to_date: str = date_utils.get_current_dt()):
    result_list = calculate_one(ts_code, share_name, to_date)
    if len(result_list) > 0:
        start_time = time.time()
        session: Session = db_client.get_session()
        for item in result_list:  # type: MqDailyIndicator
            session.add(item)
        session.flush()
        session.close()
        log.info("Insert mq_daily_indicator for %s: %s seconds" % (ts_code, time.time() - start_time))
    else:
        log.info('Nothing to insert into mq_daily_indicator %s' % ts_code)


def calculate_by_code(ts_code: str, to_date: str = date_utils.get_current_dt()):
    session: Session = db_client.get_session()
    basic: TsBasic = session.query(TsBasic).filter(TsBasic.ts_code == ts_code).one()
    session.close()
    if basic is None:
        log.error("Cant find ts_basic of %s" % ts_code)
        return
    calculate_and_insert(ts_code, basic.name, to_date)


def recalculate_by_code(ts_code: str, to_date: str = date_utils.get_current_dt()):
    session: Session = db_client.get_session()
    session.query(MqDailyIndicator).filter(MqDailyIndicator.ts_code == ts_code).delete()
    session.close()
    calculate_by_code(ts_code, to_date)


def remove_from_date(ts_code: str, from_date: str):
    session: Session = db_client.get_session()
    session.query(MqDailyIndicator).filter(MqDailyIndicator.ts_code == ts_code,
                                           MqDailyIndicator.update_date >= from_date).delete()
    session.close()

