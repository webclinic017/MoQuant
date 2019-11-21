#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time

from sqlalchemy import and_
from sqlalchemy.orm import Session

from moquant.constants import mq_calculate_start_date
from moquant.dbclient import db_client
from moquant.dbclient.mq_daily_basic import MqDailyBasic
from moquant.dbclient.mq_quarter_basic import MqQuarterBasic
from moquant.dbclient.mq_stock_mark import MqStockMark
from moquant.dbclient.mq_sys_param import MqSysParam
from moquant.dbclient.ts_basic import TsBasic
from moquant.dbclient.ts_daily_basic import TsDailyBasic
from moquant.log import get_logger
from moquant.scripts.cal_grow import cal_growing_score
from moquant.utils.datetime import format_delta, get_current_dt

log = get_logger(__name__)


def get_next_index(arr, field, current, i: int = -1):
    while i + 1 < len(arr) and getattr(arr[i + 1], field) <= current:
        i = i + 1
    return i


def calculate(ts_code: str, share_name: str, to_date: str, fix_from: str = None):
    result_list = []
    if to_date is None:
        to_date = get_current_dt()
    start_time = time.time()
    session = db_client.get_session()
    last_mq_daily = session.query(MqDailyBasic).filter(MqDailyBasic.ts_code == ts_code) \
        .order_by(MqDailyBasic.date.desc()).limit(1).all()

    from_date = mq_calculate_start_date
    if len(last_mq_daily) > 0:
        from_date = format_delta(last_mq_daily[0].date, 1)
    else:
        ts_basic_arr = session.query(TsBasic).filter(TsBasic.ts_code == ts_code).all()
        if len(ts_basic_arr) > 0 and ts_basic_arr[0].list_date > from_date:
            from_date = ts_basic_arr[0].list_date
    if fix_from is None and from_date > to_date:
        return

    # Get all daily basic from a date
    last_ts_daily = session.query(TsDailyBasic) \
        .filter(and_(TsDailyBasic.ts_code == ts_code, TsDailyBasic.trade_date < from_date)) \
        .order_by(TsDailyBasic.trade_date.desc()) \
        .limit(1) \
        .all()
    daily_start_date = last_ts_daily[0].trade_date if len(last_ts_daily) > 0 else from_date
    daily_arr = session.query(TsDailyBasic) \
        .filter(and_(TsDailyBasic.ts_code == ts_code, TsDailyBasic.trade_date >= daily_start_date)) \
        .order_by(TsDailyBasic.trade_date.asc()).all()
    if len(daily_arr) > 0 and daily_arr[0].trade_date > from_date:
        from_date = daily_arr[0].trade_date

    quarter_arr = session.query(MqQuarterBasic) \
        .filter(and_(MqQuarterBasic.ts_code == ts_code, MqQuarterBasic.update_date >= format_delta(from_date, -720))) \
        .order_by(MqQuarterBasic.update_date.asc(), MqQuarterBasic.report_period.asc(),
                  MqQuarterBasic.forecast_period.asc()) \
        .all()
    if len(quarter_arr) > 0 and quarter_arr[0].update_date > from_date:
        from_date = quarter_arr[0].update_date

    if fix_from is not None:
        from_date = fix_from

    prepare_time = time.time()
    log.info("Prepare data for %s: %s seconds" % (ts_code, prepare_time - start_time))

    d_i = get_next_index(daily_arr, 'trade_date', from_date)
    q_i = get_next_index(quarter_arr, 'update_date', from_date)

    while from_date <= to_date:
        daily_basic: TsDailyBasic = daily_arr[d_i] if 0 <= d_i < len(daily_arr) else None
        is_trade_day: bool = (daily_basic is not None and daily_basic.trade_date == from_date)
        quarter: MqQuarterBasic = quarter_arr[q_i] if 0 <= q_i < len(quarter_arr) else None

        total_share = None
        close = None
        market_value = None
        if daily_basic is not None:
            total_share = daily_basic.total_share * 10000
            close = daily_basic.close
            market_value = daily_basic.total_mv * 10000

        dprofit_period = None
        dprofit_eps = None
        dprofit_pe = None
        dprofit_peg = None
        quarter_dprofit_yoy = None
        pb = None
        if quarter is not None:
            dprofit_period = quarter.dprofit_period
            dprofit_ltm = quarter.dprofit_ltm
            if dprofit_ltm is not None and total_share is not None and total_share != 0:
                dprofit_eps = dprofit_ltm / total_share
            if dprofit_ltm is not None and market_value is not None and dprofit_ltm != 0:
                dprofit_pe = market_value / dprofit_ltm
            quarter_dprofit_yoy = quarter.quarter_dprofit_yoy
            if dprofit_pe is not None and quarter_dprofit_yoy is not None and quarter_dprofit_yoy != 0:
                dprofit_peg = dprofit_pe / quarter_dprofit_yoy / 100
            nassets = quarter.nassets
            if nassets is not None and market_value is not None and nassets != 0:
                pb = market_value / nassets

        mq_daily = MqDailyBasic(ts_code=ts_code, share_name=share_name, date=from_date, is_trade_day=is_trade_day,
                                total_share=total_share, close=close, market_value=market_value, pb=pb,
                                dprofit_period=dprofit_period, dprofit_eps=dprofit_eps,
                                quarter_dprofit_yoy=quarter_dprofit_yoy,
                                dprofit_pe=dprofit_pe, dprofit_peg=dprofit_peg,
                                grow_score=-1)
        mq_daily.grow_score = cal_growing_score(mq_daily, quarter)

        result_list.append(mq_daily)

        from_date = format_delta(from_date, 1)
        d_i = get_next_index(daily_arr, 'trade_date', from_date, d_i)
        q_i = get_next_index(quarter_arr, 'update_date', from_date)

    calculate_time = time.time()
    log.info("Calculate data for %s: %s seconds" % (ts_code, calculate_time - prepare_time))
    return result_list


def calculate_and_insert(ts_code: str, share_name: str, to_date: str):
    result_list = calculate(ts_code, share_name, to_date)
    start_time = time.time()
    session: Session = db_client.get_session()
    for item in result_list:  # type: MqDailyBasic
        session.add(item)
    session.flush()
    log.info("Insert mq daily data for %s: %s seconds" % (ts_code, time.time() - start_time))


def calculate_all():
    session: Session = db_client.get_session()
    now_date = get_current_dt()
    mq_list = session.query(MqStockMark).filter(MqStockMark.last_fetch_date == now_date).all()
    for mq in mq_list:
        calculate_and_insert(mq.ts_code, mq.share_name, mq.last_fetch_date)
    update_done_record(now_date)


def update_done_record(to_date: str):
    session: Session = db_client.get_session()
    session.merge(MqSysParam(param_key='CAL_DAILY_DONE', param_value=to_date), True)
    session.flush()


def calculate_by_code(ts_code: str):
    session: Session = db_client.get_session()
    stock: MqStockMark = session.query(MqStockMark).filter(MqStockMark.ts_code == ts_code).one()
    calculate_and_insert(ts_code, stock.share_name)


def recalculate_by_code(ts_code: str):
    session: Session = db_client.get_session()
    session.query(MqDailyBasic).filter(MqDailyBasic.ts_code == ts_code).delete()
    calculate_by_code(ts_code)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        recalculate_by_code(sys.argv[1])
    else:
        calculate_all()
