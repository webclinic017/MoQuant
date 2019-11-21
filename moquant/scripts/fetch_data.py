#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" To fetch basic data from TuShare """
import sys
import time
from sqlalchemy import and_, Column, func, Table
from sqlalchemy.orm import Session

from moquant.constants import fetch_data_start_date, mq_calculate_start_date
from moquant.dbclient import db_client
from moquant.dbclient.mq_stock_mark import MqStockMark
from moquant.dbclient.ts_adj_factor import StockAdjFactor
from moquant.dbclient.ts_balance_sheet import TsBalanceSheet
from moquant.dbclient.ts_basic import TsBasic
from moquant.dbclient.ts_cashflow import TsCashFlow
from moquant.dbclient.ts_daily_basic import TsDailyBasic
from moquant.dbclient.ts_daily_trade_info import TsDailyTradeInfo
from moquant.dbclient.ts_express import TsExpress
from moquant.dbclient.ts_fina_indicator import TsFinaIndicator
from moquant.dbclient.ts_forecast import TsForecast
from moquant.dbclient.ts_income import TsIncome
from moquant.dbclient.ts_stk_limit import TsStkLimit
from moquant.log import get_logger
from moquant.scripts import clear_after_fetch, cal_mq_quarter, cal_mq_daily, cal_grow, fetch_dividend, fetch_stk_limit
from moquant.tsclient import ts_client
from moquant.utils import threadpool
from moquant.utils.datetime import format_delta, get_current_dt
from moquant.utils.env_utils import pass_fetch_basic

log = get_logger(__name__)
threads = []


def fetch_from_date(date_column: Column, code_column: Column, ts_code: str):
    session: Session = db_client.get_session()
    result = session.query(func.max(date_column)).filter(code_column == ts_code).all()
    from_date = fetch_data_start_date
    if len(result) > 0 and not result[0][0] is None:
        from_date = format_delta(result[0][0], day_num=1)
    return from_date


def common_fetch_data(ts_code: str, api_name: str, table: Table, date_field, code_field, empty_to_end: bool = False,
                      to_date: str = get_current_dt(),
                      **kwargs):
    to_date = format_delta(to_date, 1)
    while True:
        from_date = fetch_from_date(date_field, code_field, ts_code)

        stock_data = None
        for cnt in range(2):
            log.info('To fetch %s of stock %s %s~%s' % (api_name, ts_code, from_date, to_date))
            try:
                stock_data = ts_client.fetch_data_frame(api_name, ts_code, to_date, from_date, **kwargs)
                break
            except Exception as e:
                log.error('Calling TuShare too fast. Will sleep 1 minutes...')
                time.sleep(60)

        if stock_data is None:
            return False
        elif not stock_data.empty:
            db_client.store_dataframe(stock_data, table.__tablename__)
            log.info('Successfully save %s of stock %s %s~%s' % (api_name, ts_code, from_date, to_date))
        if not empty_to_end:
            break
        elif stock_data.empty:
            break

    return True


def fetch_period_report(ts_code: str, to_date: str):
    result = True
    result = result and common_fetch_data(ts_code, 'fetch_income', TsIncome,
                                          TsIncome.ann_date, TsIncome.ts_code,
                                          to_date=to_date)
    result = result and common_fetch_data(ts_code, 'fetch_balance_sheet', TsBalanceSheet,
                                          TsBalanceSheet.ann_date, TsBalanceSheet.ts_code,
                                          to_date=to_date)
    result = result and common_fetch_data(ts_code, 'fetch_cash_flow', TsCashFlow,
                                          TsCashFlow.ann_date, TsCashFlow.ts_code,
                                          to_date=to_date)
    result = result and common_fetch_data(ts_code, 'fetch_fina_indicator', TsFinaIndicator,
                                          TsFinaIndicator.ann_date, TsFinaIndicator.ts_code,
                                          to_date=to_date)
    return result


def fetch_data_by_code(stock_code, to_date: str = get_current_dt()):
    if to_date is None:
        to_date = get_current_dt()
    result = True
    result = result and common_fetch_data(stock_code, 'fetch_daily_basic', TsDailyBasic,
                                          TsDailyBasic.trade_date, TsDailyBasic.ts_code,
                                          to_date=to_date)
    result = result and common_fetch_data(stock_code, 'fetch_daily_bar', TsDailyTradeInfo,
                                          TsDailyTradeInfo.trade_date, TsDailyTradeInfo.ts_code,
                                          to_date=to_date)
    result = result and common_fetch_data(stock_code, 'fetch_adj_factor', StockAdjFactor,
                                          StockAdjFactor.trade_date, StockAdjFactor.ts_code,
                                          to_date=to_date)
    result = result and common_fetch_data(stock_code, 'fetch_stk_limit', TsStkLimit,
                                          TsStkLimit.trade_date, TsStkLimit.ts_code,
                                          to_date=to_date)

    result = result and fetch_period_report(stock_code, to_date)

    result = result and common_fetch_data(stock_code, 'fetch_forecast', TsForecast,
                                          TsForecast.ann_date, TsForecast.ts_code,
                                          to_date=to_date)
    result = result and common_fetch_data(stock_code, 'fetch_express', TsExpress,
                                          TsExpress.ann_date, TsExpress.ts_code,
                                          to_date=to_date)

    return result


def fetch_data(to_date: str = get_current_dt()):
    if to_date is None:
        to_date = get_current_dt()
    session: Session = db_client.get_session()
    result = session.query(MqStockMark).filter(
        and_(MqStockMark.fetch_data == 1, MqStockMark.last_fetch_date < to_date)).all()
    log.info(len(result))
    for row in result:  # type: MqStockMark
        if fetch_data_by_code(row.ts_code, to_date):
            row.last_fetch_date = to_date
            session.flush()
            threadpool.submit(do_after_fetch, ts_code=row.ts_code)


def do_after_fetch(ts_code: str):
    clear_after_fetch.clear(ts_code)
    cal_mq_quarter.calculate_by_code(ts_code)
    cal_mq_daily.calculate_by_code(ts_code)


def init_stock_basic():
    if pass_fetch_basic():
        return

    # refresh stock basic every day, to update info and insert new stock
    session: Session = db_client.get_session()
    session.query(TsBasic).delete()

    stock_data = ts_client.fetch_all_stock()

    if not stock_data.empty:
        db_client.store_dataframe(stock_data, TsBasic.__tablename__)

    msm_list = session.query(MqStockMark).all()
    existed = [msm.ts_code for msm in msm_list]

    filter_df = stock_data[~stock_data['ts_code'].isin(existed)].rename(columns={"name": "stock_name"})

    to_add_obj = [
        MqStockMark(ts_code=stock.ts_code, share_name=stock.stock_name, last_daily_cal=mq_calculate_start_date,
                    fetch_data=True, last_fetch_date=fetch_data_start_date
                    ) for index, stock in filter_df.iterrows()]

    if len(to_add_obj) > 0:
        session.add_all(to_add_obj)
        session.flush()


def run(ts_code, to_date: str = get_current_dt()):
    if to_date is None:
        to_date = get_current_dt()

    threadpool.submit(fetch_dividend.update_dividend_to, dt=to_date)
    threadpool.submit(fetch_stk_limit.update_stk_limit_to, dt=to_date)

    if ts_code is not None and ts_code != '':
        session: Session = db_client.get_session()
        mq_list: MqStockMark = session.query(MqStockMark).filter(MqStockMark.ts_code == ts_code).all()
        for mq in mq_list:
            fetch_data_by_code(mq.ts_code, to_date)
            mq.last_fetch_date = to_date
            session.flush()
            threadpool.submit(do_after_fetch, ts_code=mq.ts_code)
    else:
        init_stock_basic()
        fetch_data(to_date)
    threadpool.join()
    cal_mq_daily.update_done_record(to_date)


if __name__ == '__main__':
    run(ts_code=sys.argv[1] if len(sys.argv) > 1 else None, to_date=sys.argv[2] if len(sys.argv) > 2 else None)
    exit(0)
