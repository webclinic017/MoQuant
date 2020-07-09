#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" To fetch basic data from TuShare """
import time

from sqlalchemy import Column, func, Table
from sqlalchemy.orm import Session

from moquant.constants import fetch_data_start_date
from moquant.dbclient import db_client
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
from moquant.tsclient import ts_client
from moquant.utils import compare_utils
from moquant.utils.date_utils import format_delta, get_current_dt

log = get_logger(__name__)


def fetch_from_date(date_column: Column, code_column: Column, ts_code: str):
    session: Session = db_client.get_session()
    result = session.query(func.max(date_column)).filter(code_column == ts_code).all()
    from_date = fetch_data_start_date
    if len(result) > 0 and not result[0][0] is None:
        from_date = format_delta(result[0][0], day_num=1)
    session.close()
    return from_date


def common_fetch_data(ts_code: str, api_name: str, table: Table, date_field, code_field, empty_to_end: bool = False,
                      to_date: str = get_current_dt(), to_do: bool = True,
                      **kwargs):
    if not to_do:
        return False, None
    to_date = format_delta(to_date, 1)
    from_date = fetch_from_date(date_field, code_field, ts_code)
    from_date_to_ret = None
    while True:
        stock_data = None
        for cnt in range(2):
            log.info('To fetch %s of stock %s %s~%s' % (api_name, ts_code, from_date, to_date))
            try:
                stock_data = ts_client.fetch_data_frame(api_name, ts_code, to_date, from_date, **kwargs)
                break
            except Exception as e:
                log.exception('Calling TuShare too fast. Will sleep 1 minutes...', exc_info=e)
                time.sleep(60)
                ts_client.init_token()

        if stock_data is None:
            return False, None
        elif not stock_data.empty:
            db_client.store_dataframe(stock_data, table.__tablename__)
            from_date_to_ret = from_date
            log.info('Successfully save %s of stock %s %s~%s' % (api_name, ts_code, from_date, to_date))
        if not empty_to_end:
            break
        elif stock_data.empty:
            break

    return True, from_date_to_ret


def fetch_period_report(ts_code: str, to_date: str, to_do: bool):
    if not to_do:
        return False, None
    r, d1 = common_fetch_data(ts_code, 'fetch_income', TsIncome,
                              TsIncome.ann_date, TsIncome.ts_code,
                              to_date=to_date, to_do=True)
    r, d2 = common_fetch_data(ts_code, 'fetch_balance_sheet', TsBalanceSheet,
                              TsBalanceSheet.ann_date, TsBalanceSheet.ts_code,
                              to_date=to_date, to_do=r)
    r, d3 = common_fetch_data(ts_code, 'fetch_cash_flow', TsCashFlow,
                              TsCashFlow.ann_date, TsCashFlow.ts_code,
                              to_date=to_date, to_do=r)
    r, d4 = common_fetch_data(ts_code, 'fetch_fina_indicator', TsFinaIndicator,
                              TsFinaIndicator.ann_date, TsFinaIndicator.ts_code,
                              to_date=to_date, to_do=r)
    return r, compare_utils.mini(d1, d2, d3, d4)


def fetch_data_by_code(stock_code, to_date: str = get_current_dt()):
    if to_date is None:
        to_date = get_current_dt()
    r, d1 = common_fetch_data(stock_code, 'fetch_daily_basic', TsDailyBasic,
                                          TsDailyBasic.trade_date, TsDailyBasic.ts_code,
                                          to_date=to_date, to_do=True)
    r, d2 = common_fetch_data(stock_code, 'fetch_daily_bar', TsDailyTradeInfo,
                                          TsDailyTradeInfo.trade_date, TsDailyTradeInfo.ts_code,
                                          to_date=to_date, to_do=r)
    r, d3 = common_fetch_data(stock_code, 'fetch_adj_factor', StockAdjFactor,
                                          StockAdjFactor.trade_date, StockAdjFactor.ts_code,
                                          to_date=to_date, to_do=r)

    r, d4 = fetch_period_report(stock_code, to_date, to_do=r)

    r, d5 = common_fetch_data(stock_code, 'fetch_forecast', TsForecast,
                                          TsForecast.ann_date, TsForecast.ts_code,
                                          to_date=to_date, to_do=r)
    r, d6 = common_fetch_data(stock_code, 'fetch_express', TsExpress,
                                          TsExpress.ann_date, TsExpress.ts_code,
                                          to_date=to_date, to_do=r)

    return r, compare_utils.mini(d1, d2, d3, d4, d5, d6)


def init_stock_basic():
    session: Session = db_client.get_session()
    session.query(TsBasic).delete()

    stock_data = ts_client.fetch_all_stock()

    if not stock_data.empty:
        db_client.store_dataframe(stock_data, TsBasic.__tablename__)
