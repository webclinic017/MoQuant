#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Interact with TuShare """
from operator import methodcaller

import tushare as ts
from pandas import DataFrame
from tushare.pro.client import DataApi

from moquant.log import get_logger
from moquant.utils import json_utils

log = get_logger(__name__)


class TsClient(object):
    __ts: ts = None
    __pro: DataApi = None

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '__inst'):
            cls.__inst = super(TsClient, cls).__new__(cls, *args, **kwargs)
            cls.__inst.__ts = ts
            info_json = json_utils.from_file('/resources/ts.json')
            cls.__inst.__ts.set_token(info_json['token'])
            log.info('Init tushare token successfully')
            cls.__inst.__pro = cls.__inst.__ts.pro_api()
        return cls.__inst

    def fetch_all_stock(self) -> DataFrame:
        return self.__pro.stock_basic()

    # 每分钟200次
    def fetch_daily_bar(self, ts_code: str, end_date: str, start_date: str) -> DataFrame:
        return self.__ts.pro_bar(ts_code=ts_code, start_date=start_date, end_date=end_date)

    def fetch_daily_basic(self, ts_code: str, end_date: str, start_date: str) -> DataFrame:
        return self.__pro.daily_basic(ts_code=ts_code, start_date=start_date, end_date=end_date)

    def fetch_adj_factor(self, ts_code: str, end_date: str, start_date: str) -> DataFrame:
        return self.__pro.adj_factor(ts_code=ts_code, start_date=start_date, end_date=end_date)

    def fetch_income(self, ts_code: str, end_date: str, start_date: str) -> DataFrame:
        return self.__pro.income(ts_code=ts_code, start_date=start_date, end_date=end_date)

    def fetch_balance_sheet(self, ts_code: str, end_date: str, start_date: str) -> DataFrame:
        return self.__pro.balancesheet(ts_code=ts_code, start_date=start_date, end_date=end_date)

    def fetch_cash_flow(self, ts_code: str, end_date: str, start_date: str) -> DataFrame:
        return self.__pro.cashflow(ts_code=ts_code, start_date=start_date, end_date=end_date)

    def fetch_forecast(self, ts_code: str, end_date: str, start_date: str) -> DataFrame:
        return self.__pro.forecast(ts_code=ts_code, start_date=start_date, end_date=end_date)

    def fetch_express(self, ts_code: str, end_date: str, start_date: str) -> DataFrame:
        return self.__pro.express(ts_code=ts_code, start_date=start_date, end_date=end_date)

    def fetch_data_frame(self, method_name: str, ts_code: str, end_date: str,
                         start_date: str = '19910101') -> DataFrame:
        func = methodcaller(method_name, ts_code=ts_code, start_date=start_date, end_date=end_date)
        return func(self)


ts_client = TsClient()
