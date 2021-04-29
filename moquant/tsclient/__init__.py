#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Interact with TuShare """
import math
from operator import methodcaller

import pandas
import tushare as ts
from pandas import DataFrame
from tushare.pro.client import DataApi

from moquant.log import get_logger
from moquant.utils import decimal_utils, date_utils
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
        token = get_env_value('TS_TOKEN')
        self.__ts.set_token(token)
        log.info('Init tushare token successfully: %s' % token)
        self.__pro = self.__ts.pro_api()

    def fetch_all_stock(self) -> DataFrame:
        return self.__pro.stock_basic(fields='ts_code,symbol,name,area,industry,list_date,exchange')

    # 每分钟200次
    def fetch_daily_bar(self, ts_code: str, end_date: str, start_date: str) -> DataFrame:
        return self.__ts.pro_bar(ts_code=ts_code, start_date=start_date, end_date=end_date)

    def fetch_daily_basic(self, ts_code: str, end_date: str, start_date: str) -> DataFrame:
        df: DataFrame = self.__pro.daily_basic(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if not df.empty:
            # 按日期升序
            df = df.sort_values(by='trade_date')
            df.loc[:, 'turnover_rate'] = df.apply(lambda row: decimal_utils.none_to_zero(row.turnover_rate), axis=1)
            df.loc[:, 'volume_ratio'] = df.apply(lambda row: decimal_utils.none_to_zero(row.volume_ratio), axis=1)

            # 替换掉所有需要是0的之后，取最近的值填充
            df = df.ffill()
            df.loc[:, 'total_share'] = df.apply(lambda row:
                                                decimal_utils.mul(row.total_share, 10000, err_default=None), axis=1)
            df.loc[:, 'float_share'] = df.apply(lambda row:
                                                decimal_utils.mul(row.float_share, 10000, err_default=None), axis=1)
            df.loc[:, 'free_share'] = df.apply(lambda row:
                                               decimal_utils.mul(row.free_share, 10000, err_default=None), axis=1)
            df.loc[:, 'free_share'] = df.apply(lambda row:
                                               row.float_share if row.free_share is None or math.isnan(row.free_share)
                                               else row.free_share, axis=1)
            df.loc[:, 'total_mv'] = df.apply(lambda row:
                                             decimal_utils.mul(row.total_mv, 10000, err_default=None), axis=1)

        return df

    def fetch_adj_factor(self, ts_code: str, end_date: str, start_date: str) -> DataFrame:
        return self.__pro.adj_factor(ts_code=ts_code, start_date=start_date, end_date=end_date)

    def fetch_income(self, ts_code: str, end_date: str, start_date: str) -> DataFrame:
        df1: DataFrame = self.__pro.income(ts_code=ts_code, start_date=start_date, end_date=end_date, report_type=1)
        df2: DataFrame = self.__pro.income(ts_code=ts_code, start_date=start_date, end_date=end_date, report_type=4)
        df: DataFrame = df1.append(df2)
        if not df.empty:
            df.loc[:, 'mq_ann_date'] = df.apply(lambda row: mini(row.ann_date, row.f_ann_date), axis=1)
            # 资产减值损失 - 2019Q2开始计入其他收益，应该为负数，不可转回。2019Q2之前为成本，所以需要取反
            df.loc[:, 'assets_impair_loss'] = df.apply(lambda row: decimal_utils.none_to_zero(row.assets_impair_loss),
                                                       axis=1)
            df.loc[:, 'assets_impair_loss'] = df.apply(
                lambda row: decimal_utils.negative(row.assets_impair_loss) if row.end_date < '20190630' or (
                        row.end_date >= '20190630' and row.assets_impair_loss > 0) else row.assets_impair_loss,
                axis=1)
        return df

    def fetch_balance_sheet(self, ts_code: str, end_date: str, start_date: str) -> DataFrame:
        df1 = self.__pro.balancesheet(ts_code=ts_code, start_date=start_date, end_date=end_date, report_type=1)
        df2 = self.__pro.balancesheet(ts_code=ts_code, start_date=start_date, end_date=end_date, report_type=4)
        df = df1.append(df2)
        if not df.empty:
            df.loc[:, 'mq_ann_date'] = df.apply(lambda row: mini(row.ann_date, row.f_ann_date), axis=1)
            df.loc[:, 'notes_receiv'] = df.apply(lambda row: decimal_utils.none_to_zero(row.notes_receiv), axis=1)
            df.loc[:, 'accounts_receiv'] = df.apply(lambda row: decimal_utils.none_to_zero(row.accounts_receiv), axis=1)
            df.loc[:, 'lt_rec'] = df.apply(lambda row: decimal_utils.none_to_zero(row.lt_rec), axis=1)
            df.loc[:, 'oth_receiv'] = df.apply(lambda row: decimal_utils.none_to_zero(row.oth_receiv), axis=1)
            df.loc[:, 'div_receiv'] = df.apply(lambda row: decimal_utils.none_to_zero(row.div_receiv), axis=1)
            df.loc[:, 'int_receiv'] = df.apply(lambda row: decimal_utils.none_to_zero(row.int_receiv), axis=1)
            df.loc[:, 'notes_payable'] = df.apply(lambda row: decimal_utils.none_to_zero(row.notes_payable), axis=1)
            df.loc[:, 'acct_payable'] = df.apply(lambda row: decimal_utils.none_to_zero(row.acct_payable), axis=1)
            df.loc[:, 'total_nca'] = df.apply(lambda row: decimal_utils.none_to_zero(row.total_nca), axis=1)
            df.loc[:, 'fa_avail_for_sale'] = df.apply(lambda row: decimal_utils.none_to_zero(row.fa_avail_for_sale),
                                                      axis=1)
            df.loc[:, 'total_cur_liab'] = df.apply(lambda row: decimal_utils.none_to_zero(row.total_cur_liab), axis=1)
            df.loc[:, 'total_cur_assets'] = df.apply(lambda row: decimal_utils.none_to_zero(row.total_cur_assets), axis=1)
            df.loc[:, 'lt_borr'] = df.apply(lambda row: decimal_utils.none_to_zero(row.lt_borr), axis=1)
            df.loc[:, 'st_borr'] = df.apply(lambda row: decimal_utils.none_to_zero(row.st_borr), axis=1)
            df.loc[:, 'money_cap'] = df.apply(lambda row: decimal_utils.none_to_zero(row.money_cap), axis=1)
            df.loc[:, 'oth_cur_assets'] = df.apply(lambda row: decimal_utils.none_to_zero(row.oth_cur_assets), axis=1)
            # 待摊费用(新会计准则取消) -> 长期待摊费用
            df.loc[:, 'lt_amor_exp'] = df.apply(lambda row: decimal_utils.add(row.amor_exp, row.lt_amor_exp), axis=1)
        return df

    def fetch_cash_flow(self, ts_code: str, end_date: str, start_date: str) -> DataFrame:
        df1 = self.__pro.cashflow(ts_code=ts_code, start_date=start_date, end_date=end_date, report_type=1)
        df2 = self.__pro.cashflow(ts_code=ts_code, start_date=start_date, end_date=end_date, report_type=4)
        df = df1.append(df2)
        if not df.empty:
            df.loc[:, 'mq_ann_date'] = df.apply(lambda row: mini(row.ann_date, row.f_ann_date), axis=1)
            df.loc[:, 'prov_depr_assets'] = df.apply(lambda row: decimal_utils.none_to_zero(row.prov_depr_assets),
                                                     axis=1)
            df.loc[:, 'depr_fa_coga_dpba'] = df.apply(lambda row: decimal_utils.none_to_zero(row.depr_fa_coga_dpba),
                                                      axis=1)
            df.loc[:, 'amort_intang_assets'] = df.apply(lambda row: decimal_utils.none_to_zero(row.amort_intang_assets),
                                                        axis=1)
            df.loc[:, 'lt_amort_deferred_exp'] = df.apply(
                lambda row: decimal_utils.none_to_zero(row.lt_amort_deferred_exp), axis=1)
            df.loc[:, 'loss_scr_fa'] = df.apply(lambda row: decimal_utils.none_to_zero(row.loss_scr_fa), axis=1)
        return df

    def fetch_forecast(self, ts_code: str, end_date: str = None, start_date: str= None) -> DataFrame:
        df: DataFrame = self.__pro.forecast(ts_code=ts_code, start_date=start_date, end_date=end_date)
        return self.__handle_forecast(self.__replace_nan(df))

    def fetch_forecast_by_date(self, ann_date: str) -> DataFrame:
        return self.__handle_forecast(self.__pro.forecast(ann_date=ann_date))

    def __handle_forecast(self, df: DataFrame):
        if not df.empty:
            df.loc[:, 'net_profit_min'] = df.apply(lambda row:
                                                   decimal_utils.mul(row.net_profit_min, 10000, err_default=None),
                                                   axis=1)
            df.loc[:, 'net_profit_max'] = df.apply(lambda row:
                                                   decimal_utils.mul(row.net_profit_max, 10000, err_default=None),
                                                   axis=1)
            df.loc[:, 'last_parent_net'] = df.apply(lambda row:
                                                    decimal_utils.mul(row.last_parent_net, 10000, err_default=None),
                                                    axis=1)
        return df

    def __replace_nan(self, df: DataFrame):
        return df.where(pandas.notnull(df), None)

    def fetch_express(self, ts_code: str, end_date: str = None, start_date: str = None) -> DataFrame:
        return self.__pro.express(ts_code=ts_code, start_date=start_date, end_date=end_date)

    def fetch_fina_indicator(self, ts_code: str, end_date: str, start_date: str) -> DataFrame:
        return self.__pro.fina_indicator(ts_code=ts_code, start_date=start_date, end_date=end_date)

    def fetch_data_frame(self, method_name: str, ts_code: str, end_date: str,
                         start_date: str = '19910101', **kwargs) -> DataFrame:
        func = methodcaller(method_name, ts_code=ts_code, start_date=start_date, end_date=end_date, **kwargs)
        return func(self)

    def fetch_disclosure_date(self, date: str) -> DataFrame:
        return self.__pro.disclosure_date(pre_date=date)

    def fetch_trade_cal(self, exchange: str = None, start_date=None, end_date=None, is_open=None) -> DataFrame:
        return self.__pro.trade_cal(exchange=exchange, start_date=start_date, end_date=end_date, is_open=is_open)

    def fetch_dividend(self, ts_code: str = None, imp_ann_date: str = None) -> DataFrame:
        df: DataFrame = self.__pro.dividend(ts_code=ts_code, imp_ann_date=imp_ann_date)
        df = df[df['div_proc'] == '实施']
        if not df.empty:
            df['is_fix'] = 0
            df.loc[:, 'imp_ann_date'] = df.apply(lambda row:
                                                 row.end_date if row.imp_ann_date is None else row.imp_ann_date,
                                                 axis=1)
            # df.loc[:, 'end_date'] = df.apply(lambda row: date_utils.latest_period_date(row.end_date), axis=1)
            df = df.astype({"imp_ann_date": str})
        return df

    def fetch_stk_limit(self, ts_code: str = None, trade_date: str = None, start_date: str = None,
                        end_date: str = None):
        return self.__pro.stk_limit(ts_code=ts_code, trade_date=trade_date, start_date=start_date, end_date=end_date)

    def get_pro(self):
        return self.__pro

    def get_ts(self):
        return self.__ts


ts_client = TsClient()

if __name__ == '__main__':
    a = ts_client.fetch_express(ts_code='601318.SH', start_date='20200101', end_date='20200131')
    pass
