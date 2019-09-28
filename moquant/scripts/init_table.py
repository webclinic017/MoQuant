#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" To init table, will not create if table exists """

import moquant.dbclient as client
from moquant.dbclient.base import Base
from moquant.dbclient.mq_basic_all import MqStockBasicAll
from moquant.dbclient.mq_stock_mark import MqStockMark
from moquant.dbclient.ts_adj_factor import StockAdjFactor
from moquant.dbclient.ts_balance_sheet import StockBalanceSheet
from moquant.dbclient.ts_basic import StockBasic
from moquant.dbclient.ts_cashflow import StockCashFlow
from moquant.dbclient.ts_daily_basic import TsStockDailyBasic
from moquant.dbclient.ts_daily_trade_info import StockDailyTradeInfo
from moquant.dbclient.ts_express import StockExpress
from moquant.dbclient.ts_forecast import StockForecast
from moquant.dbclient.ts_income import StockIncome


def create_table():
    engine = client.db_client.get_engine()
    all_table = [MqStockMark, MqStockBasicAll,
                 StockBasic, TsStockDailyBasic, StockDailyTradeInfo, StockAdjFactor,
                 StockIncome, StockBalanceSheet, StockCashFlow, StockForecast, StockExpress]

    # Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


if __name__ == '__main__':
    create_table()
