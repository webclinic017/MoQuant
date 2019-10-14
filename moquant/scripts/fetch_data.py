#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" To fetch basic data from TuShare """
import _thread
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
from moquant.log import get_logger
from moquant.scripts import clear_after_fetch, cal_mq_quarter, cal_mq_daily
from moquant.tsclient import ts_client
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
                      **kwargs):
    while True:
        to_date = format_delta(get_current_dt(), 1)
        from_date = fetch_from_date(date_field, code_field, ts_code)

        stock_data = None
        for cnt in range(2):
            log.info('To fetch %s of stock %s %s~%s' % (api_name, ts_code, from_date, to_date))
            try:
                stock_data = ts_client.fetch_data_frame(api_name, ts_code, to_date, from_date, **kwargs)
                break
            except Exception as e:
                log.error(e)
                time.sleep(60)

        if stock_data is None:
            return False
        elif not stock_data.empty:
            db_client.store_dataframe(stock_data, table.__tablename__)
            print('Successfully save %s of stock %s %s~%s' % (api_name, ts_code, from_date, to_date))
        if not empty_to_end:
            break
        elif stock_data.empty:
            break

    return True


def fetch_data_by_code(stock_code):
    result = True
    result = result and common_fetch_data(stock_code, 'fetch_daily_basic', TsDailyBasic,
                                          TsDailyBasic.trade_date, TsDailyBasic.ts_code)
    result = result and common_fetch_data(stock_code, 'fetch_daily_bar', TsDailyTradeInfo,
                                          TsDailyTradeInfo.trade_date, TsDailyTradeInfo.ts_code)
    result = result and common_fetch_data(stock_code, 'fetch_adj_factor', StockAdjFactor,
                                          StockAdjFactor.trade_date, StockAdjFactor.ts_code)
    result = result and common_fetch_data(stock_code, 'fetch_income', TsIncome,
                                          TsIncome.ann_date, TsIncome.ts_code)
    result = result and common_fetch_data(stock_code, 'fetch_balance_sheet', TsBalanceSheet,
                                          TsBalanceSheet.ann_date, TsBalanceSheet.ts_code)
    result = result and common_fetch_data(stock_code, 'fetch_cash_flow', TsCashFlow,
                                          TsCashFlow.ann_date, TsCashFlow.ts_code)
    result = result and common_fetch_data(stock_code, 'fetch_forecast', TsForecast,
                                          TsForecast.ann_date, TsForecast.ts_code)
    result = result and common_fetch_data(stock_code, 'fetch_express', TsExpress,
                                          TsExpress.ann_date, TsExpress.ts_code)
    result = result and common_fetch_data(stock_code, 'fetch_fina_indicator', TsFinaIndicator,
                                          TsFinaIndicator.ann_date, TsFinaIndicator.ts_code)
    return result


def fetch_data():
    session: Session = db_client.get_session()
    result = session.query(MqStockMark).filter(
        and_(MqStockMark.fetch_data == 1, MqStockMark.last_fetch_date < get_current_dt())).all()
    log.info(len(result))
    for row in result:  # type: MqStockMark
        if fetch_data_by_code(row.ts_code):
            row.last_fetch_date = get_current_dt()
            session.flush()
            do_after_fetch(row.ts_code)
            # _thread.start_new_thread(do_after_fetch, (row.ts_code,))


def do_after_fetch(ts_code:str) :
    clear_after_fetch.clear(ts_code)
    cal_mq_quarter.run(ts_code)
    cal_mq_daily.run(ts_code)


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


def run(ts_code):
    if ts_code is not None and ts_code != '':
        session: Session = db_client.get_session()
        mq_list: MqStockMark = session.query(MqStockMark).filter(MqStockMark.ts_code == sys.argv[1]).all()
        for mq in mq_list:
            fetch_data_by_code(mq.ts_code)
            mq.last_fetch_date = get_current_dt()
            session.flush()
    else:
        init_stock_basic()
        fetch_data()
        clear_after_fetch.clear(None)
        cal_mq_quarter.calculate_all()
        cal_mq_daily.calculate_all()


if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else None)
