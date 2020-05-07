#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Interact with TuShare """
from operator import methodcaller

import tushare as ts
from pandas import DataFrame
from tushare.pro.client import DataApi

from moquant.log import get_logger
from moquant.utils import decimal_utils
from moquant.utils.compare_utils import mini
from moquant.utils.env_utils import get_env_value

log = get_logger(__name__)


class TsClient(object):
    __ts: ts = None
    __pro: DataApi = None

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '__inst'):
            cls.__inst = super(TsClient, cls).__new__(cls, *args, **kwargs)
            cls.__inst.__ts = ts
            cls.__inst.init_token()
        return cls.__inst

    def init_token(self):
        self.__ts.set_token(get_env_value('TS_TOKEN'))
        log.info('Init tushare token successfully')
        self.__pro = self.__ts.pro_api()

    def fetch_all_stock(self) -> DataFrame:
        return self.__pro.stock_basic()

    # 每分钟200次
    def fetch_daily_bar(self, ts_code: str, end_date: str, start_date: str) -> DataFrame:
        return self.__ts.pro_bar(ts_code=ts_code, start_date=start_date, end_date=end_date)

    def fetch_daily_basic(self, ts_code: str, end_date: str, start_date: str) -> DataFrame:
        df: DataFrame = self.__pro.daily_basic(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if not df.empty:
            df['total_share'] = df.apply(lambda row:
                                         decimal_utils.mul(row.total_share, 10000, err_default=None), axis=1)
            df['total_mv'] = df.apply(lambda row:
                                      decimal_utils.mul(row.total_mv, 10000, err_default=None), axis=1)
        return df

    def fetch_adj_factor(self, ts_code: str, end_date: str, start_date: str) -> DataFrame:
        return self.__pro.adj_factor(ts_code=ts_code, start_date=start_date, end_date=end_date)

    def fetch_income(self, ts_code: str, end_date: str, start_date: str) -> DataFrame:
        df1: DataFrame = self.__pro.income(ts_code=ts_code, start_date=start_date, end_date=end_date, report_type=1)
        df2: DataFrame = self.__pro.income(ts_code=ts_code, start_date=start_date, end_date=end_date, report_type=4)
        df: DataFrame = df1.append(df2)
        if not df.empty:
            df['mq_ann_date'] = df.apply(lambda row: mini(row.ann_date, row.f_ann_date), axis=1)
        return df

    def fetch_balance_sheet(self, ts_code: str, end_date: str, start_date: str) -> DataFrame:
        df1 = self.__pro.balancesheet(ts_code=ts_code, start_date=start_date, end_date=end_date, report_type=1)
        df2 = self.__pro.balancesheet(ts_code=ts_code, start_date=start_date, end_date=end_date, report_type=4)
        df = df1.append(df2)
        if not df.empty:
            df['mq_ann_date'] = df.apply(lambda row: mini(row.ann_date, row.f_ann_date), axis=1)
            df['notes_receiv'] = df.apply(lambda row: 0 if row.notes_receiv is None else row.notes_receiv, axis=1)
            df['accounts_receiv'] = df.apply(lambda row: 0 if row.accounts_receiv is None else row.accounts_receiv, axis=1)
            df['oth_receiv'] = df.apply(lambda row: 0 if row.oth_receiv is None else row.oth_receiv, axis=1)
            df['lt_rec'] = df.apply(lambda row: 0 if row.lt_rec is None else row.lt_rec, axis=1)
        return df

    def fetch_cash_flow(self, ts_code: str, end_date: str, start_date: str) -> DataFrame:
        df1 = self.__pro.cashflow(ts_code=ts_code, start_date=start_date, end_date=end_date, report_type=1)
        df2 = self.__pro.cashflow(ts_code=ts_code, start_date=start_date, end_date=end_date, report_type=4)
        df = df1.append(df2)
        if not df.empty:
            df['mq_ann_date'] = df.apply(lambda row: mini(row.ann_date, row.f_ann_date), axis=1)
        return df

    def fetch_forecast(self, ts_code: str, end_date: str, start_date: str) -> DataFrame:
        return self._handle_forecast(self.__pro.forecast(ts_code=ts_code, start_date=start_date, end_date=end_date))

    def fetch_forecast_by_date(self, ann_date: str) -> DataFrame:
        return self._handle_forecast(self.__pro.forecast(ann_date=ann_date))

    def _handle_forecast(self, df: DataFrame):
        if not df.empty:
            df['net_profit_min'] = df.apply(lambda row:
                                            decimal_utils.mul(row.net_profit_min, 10000, err_default=None), axis=1)
            df['net_profit_max'] = df.apply(lambda row:
                                            decimal_utils.mul(row.net_profit_max, 10000, err_default=None), axis=1)
            df['last_parent_net'] = df.apply(lambda row:
                                             decimal_utils.mul(row.last_parent_net, 10000, err_default=None), axis=1)
        return df

    def fetch_express(self, ts_code: str, end_date: str, start_date: str) -> DataFrame:
        return self.__pro.express(ts_code=ts_code, start_date=start_date, end_date=end_date)

    def fetch_fina_indicator(self, ts_code: str, end_date: str, start_date: str) -> DataFrame:
        return self.__pro.fina_indicator(ts_code=ts_code, start_date=start_date, end_date=end_date)

    def fetch_data_frame(self, method_name: str, ts_code: str, end_date: str,
                         start_date: str = '19910101', **kwargs) -> DataFrame:
        func = methodcaller(method_name, ts_code=ts_code, start_date=start_date, end_date=end_date, **kwargs)
        return func(self)

    def fetch_disclosure_date(self, date: str) -> DataFrame:
        return self.__pro.disclosure_date(pre_date=date)

    def fetch_trade_cal(self, start_date=None, end_date=None, is_open=None) -> DataFrame:
        df1: DataFrame = self.__pro.trade_cal(exchange='SSE', start_date=start_date, end_date=end_date, is_open=is_open)
        df2: DataFrame = self.__pro.trade_cal(exchange='SZSE', start_date=start_date, end_date=end_date,
                                              is_open=is_open)
        return df1.append(df2)

    def fetch_dividend(self, ts_code: str = None, ann_date: str = None) -> DataFrame:
        return self.__pro.dividend(ts_code=ts_code, ann_date=ann_date)

    def fetch_stk_limit(self, ts_code: str = None, trade_date: str = None, start_date: str = None,
                        end_date: str = None):
        return self.__pro.stk_limit(ts_code=ts_code, trade_date=trade_date, start_date=start_date, end_date=end_date)


ts_client = TsClient()
