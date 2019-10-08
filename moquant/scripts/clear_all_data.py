#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

from moquant.constants import fetch_data_start_date
from moquant.dbclient import db_client
from moquant.dbclient.mq_daily_basic import MqDailyBasic
from moquant.dbclient.mq_stock_mark import MqStockMark
from moquant.dbclient.ts_adj_factor import StockAdjFactor
from moquant.dbclient.ts_balance_sheet import TsBalanceSheet
from moquant.dbclient.ts_cashflow import TsCashFlow
from moquant.dbclient.ts_daily_basic import TsDailyBasic
from moquant.dbclient.ts_daily_trade_info import TsDailyTradeInfo
from moquant.dbclient.ts_express import TsExpress
from moquant.dbclient.ts_fina_indicator import TsFinaIndicator
from moquant.dbclient.ts_forecast import TsForecast
from moquant.dbclient.ts_income import TsIncome


def clear(ts_code: str):
    if ts_code is None:
        return
    session = db_client.get_session()
    session.query(MqDailyBasic).filter(MqDailyBasic.ts_code == ts_code).delete()
    session.query(StockAdjFactor).filter(StockAdjFactor.ts_code == ts_code).delete()
    session.query(TsBalanceSheet).filter(TsBalanceSheet.ts_code == ts_code).delete()
    session.query(TsCashFlow).filter(TsCashFlow.ts_code == ts_code).delete()
    session.query(TsDailyBasic).filter(TsDailyBasic.ts_code == ts_code).delete()
    session.query(TsDailyTradeInfo).filter(TsDailyTradeInfo.ts_code == ts_code).delete()
    session.query(TsExpress).filter(TsExpress.ts_code == ts_code).delete()
    session.query(TsForecast).filter(TsForecast.ts_code == ts_code).delete()
    session.query(TsIncome).filter(TsIncome.ts_code == ts_code).delete()
    session.query(TsFinaIndicator).filter(TsFinaIndicator.ts_code == ts_code).delete()

    mark_arr = session.query(MqStockMark).filter(MqStockMark.ts_code == ts_code).all()
    if len(mark_arr) > 0:
        mark: MqStockMark = mark_arr[0]
        mark.last_fetch_date = fetch_data_start_date
        session.add(mark)
        session.flush()


if __name__ == '__main__':
    clear(sys.argv[1])
