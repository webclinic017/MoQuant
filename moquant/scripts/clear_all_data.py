#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

from moquant.constants import fetch_data_start_date
from moquant.dbclient import db_client
from moquant.dbclient.mq_basic_all import MqStockBasicAll
from moquant.dbclient.mq_stock_mark import MqStockMark
from moquant.dbclient.ts_adj_factor import StockAdjFactor
from moquant.dbclient.ts_balance_sheet import StockBalanceSheet
from moquant.dbclient.ts_cashflow import StockCashFlow
from moquant.dbclient.ts_daily_basic import TsStockDailyBasic
from moquant.dbclient.ts_daily_trade_info import StockDailyTradeInfo
from moquant.dbclient.ts_express import StockExpress
from moquant.dbclient.ts_forecast import StockForecast
from moquant.dbclient.ts_income import StockIncome


def clear(ts_code: str):
    if ts_code is None:
        return
    session = db_client.get_session()
    session.query(MqStockBasicAll).filter(MqStockBasicAll.ts_code == ts_code).delete()
    session.query(StockAdjFactor).filter(StockAdjFactor.ts_code == ts_code).delete()
    session.query(StockBalanceSheet).filter(StockBalanceSheet.ts_code == ts_code).delete()
    session.query(StockCashFlow).filter(StockCashFlow.ts_code == ts_code).delete()
    session.query(TsStockDailyBasic).filter(TsStockDailyBasic.ts_code == ts_code).delete()
    session.query(StockDailyTradeInfo).filter(StockDailyTradeInfo.ts_code == ts_code).delete()
    session.query(StockExpress).filter(StockExpress.ts_code == ts_code).delete()
    session.query(StockForecast).filter(StockForecast.ts_code == ts_code).delete()
    session.query(StockIncome).filter(StockIncome.ts_code == ts_code).delete()

    mark_arr = session.query(MqStockMark).filter(MqStockMark.ts_code == ts_code).all()
    if len(mark_arr) > 0:
        mark: MqStockMark = mark_arr[0]
        mark.last_handle_date = fetch_data_start_date
        session.add(mark)
        session.flush()


if __name__ == '__main__':
    clear(sys.argv[1])
