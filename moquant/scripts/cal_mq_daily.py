#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

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
from moquant.utils.datetime import format_delta, get_current_dt

log = get_logger(__name__)


def get_next_index(arr, field, current, i: int = -1):
    while i + 1 < len(arr) and getattr(arr[i + 1], field) <= current:
        i = i + 1
    return i


def calculate(ts_code: str, share_name: str):
    now_date = get_current_dt()
    session = db_client.get_session()
    last_basic_arr = session.query(MqDailyBasic).filter(MqDailyBasic.ts_code == ts_code) \
        .order_by(MqDailyBasic.date.desc()).limit(1).all()
    last_basic = None
    if len(last_basic_arr) > 0:
        last_basic = last_basic_arr[0]

    from_date = mq_calculate_start_date
    if last_basic is not None:
        from_date = format_delta(last_basic.date, 1)
    else:
        ts_basic_arr = session.query(TsBasic).filter(TsBasic.ts_code == ts_code).all()
        if len(ts_basic_arr) > 0 and ts_basic_arr[0].list_date > from_date:
            from_date = ts_basic_arr[0].list_date
    if from_date > now_date:
        return

    # Get all daily basic from a date
    last_daily_basic = session.query(TsDailyBasic) \
        .filter(and_(TsDailyBasic.ts_code == ts_code, TsDailyBasic.trade_date < from_date)) \
        .order_by(TsDailyBasic.trade_date.desc()) \
        .limit(1) \
        .all()
    daily_start_date = last_daily_basic[0].trade_date if len(last_daily_basic) > 0 else from_date
    daily_arr = session.query(TsDailyBasic) \
        .filter(and_(TsDailyBasic.ts_code == ts_code, TsDailyBasic.trade_date >= daily_start_date)) \
        .order_by(TsDailyBasic.trade_date.asc()).all()
    if len(daily_arr) > 0 and daily_arr[0].trade_date > from_date:
        from_date = daily_arr[0].trade_date

    quarter_arr = session.query(MqQuarterBasic) \
        .filter(and_(MqQuarterBasic.ts_code == ts_code, MqQuarterBasic.update_date >= from_date)) \
        .order_by(MqQuarterBasic.update_date.asc(), MqQuarterBasic.report_period.asc(),
                  MqQuarterBasic.forecast_period.asc()) \
        .all()
    if len(quarter_arr) > 0 and quarter_arr[0].update_date > from_date:
        from_date = quarter_arr[0].update_date

    d_i = get_next_index(daily_arr, 'trade_date', from_date)
    q_i = get_next_index(quarter_arr, 'update_date', from_date)

    while from_date <= now_date:
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

        session.add(MqDailyBasic(ts_code=ts_code, share_name=share_name, date=from_date, is_trade_day=is_trade_day,
                                 total_share=total_share, close=close, market_value=market_value, pb=pb,
                                 dprofit_period=dprofit_period, dprofit_eps=dprofit_eps,
                                 quarter_dprofit_yoy=quarter_dprofit_yoy,
                                 dprofit_pe=dprofit_pe, dprofit_peg=dprofit_peg))

        from_date = format_delta(from_date, 1)
        d_i = get_next_index(daily_arr, 'trade_date', from_date, d_i)
        q_i = get_next_index(quarter_arr, 'update_date', from_date)

    session.flush()


def calculate_all():
    session: Session = db_client.get_session()
    now_date = get_current_dt()
    mq_list: MqStockMark = session.query(MqStockMark).filter(MqStockMark.last_fetch_date == now_date).all()
    for mq in mq_list:
        calculate(mq.ts_code, mq.share_name)
    param = session.query(MqSysParam).filter(MqSysParam.param_key == 'CAL_DAILY_DONE').all()
    if len(param) > 0:
        param[0].value = now_date
    else:
        session.add(MqSysParam(param_key='CAL_DAILY_DONE', param_value=now_date))
    session.flush()


def run(ts_code: str):
    if ts_code is not None:
        session: Session = db_client.get_session()
        mq_list: MqStockMark = session.query(MqStockMark).filter(MqStockMark.ts_code == ts_code).all()
        for mq in mq_list:
            calculate(mq.ts_code, mq.share_name)
    else:
        calculate_all()


if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else None)
