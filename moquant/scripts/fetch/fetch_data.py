#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" To fetch basic data from TuShare """
import time

from sqlalchemy import func, Table
from sqlalchemy.orm import Session

from moquant.constants import fetch_data_start_date
from moquant.dbclient import db_client
from moquant.dbclient.ts_adj_factor import TsAdjFactor
from moquant.dbclient.ts_balance_sheet import TsBalanceSheet
from moquant.dbclient.ts_cashflow import TsCashFlow
from moquant.dbclient.ts_daily_basic import TsDailyBasic
from moquant.dbclient.ts_daily_trade_info import TsDailyTradeInfo
from moquant.dbclient.ts_express import TsExpress
from moquant.dbclient.ts_fina_indicator import TsFinaIndicator
from moquant.dbclient.ts_forecast import TsForecast
from moquant.dbclient.ts_income import TsIncome
from moquant.dbclient.ts_stk_limit import TsStkLimit
from moquant.log import get_logger
from moquant.tsclient import ts_client
from moquant.utils import compare_utils, date_utils

log = get_logger(__name__)


def fetch_from_date(date_column: dict(type=str, help='对应发布日期的字段名 用于获取该类型数据在DB中最新日期'),
                    code_column: dict(type=str, help='对应股票编码的字段名'),
                    ts_code: dict(type=str, help='股票编码')):
    session: Session = db_client.get_session()
    result = session.query(func.max(date_column)).filter(code_column == ts_code).all()
    from_date = fetch_data_start_date
    if len(result) > 0 and not result[0][0] is None:
        from_date = date_utils.format_delta(result[0][0], day_num=1)
    session.close()
    return from_date


def common_fetch_data(ts_code: str, api_name: str, table: Table,
                      date_field: str, code_field: str,
                      to_date: str = date_utils.get_current_dt(), to_do: bool = True,
                      page_size: int = 1000,
                      **kwargs):
    """
    :param ts_code: 股票编码
    :param api_name: 调用tsclient的方法名
    :param table: sqlalchemy的表定义
    :param date_field: 对应发布日期的字段名 用于获取该类型数据在DB中最新日期
    :param code_field: 对应股票编码的字段名
    :param to_date: 数据要获取到哪天
    :param to_do: 是否要进行此次获取
    :param page_size: 每次获取多少条数据
    :param kwargs:
    :return:
    """
    if not to_do:
        return False, None
    # 财报的 end_date 是第二天，不过目前是没有那么快有数据的
    to_date = date_utils.format_delta(to_date, 1)
    from_date = fetch_from_date(date_field, code_field, ts_code)
    from_date_to_ret = None
    while from_date < to_date:
        stock_data = None
        next_date = date_utils.format_delta(from_date, page_size)
        for cnt in range(2):
            log.info('To fetch %s of stock %s %s~%s' % (table.__tablename__, ts_code, from_date, next_date))
            try:
                stock_data = ts_client.fetch_data_frame(api_name, ts_code, next_date, from_date, **kwargs)
                break
            except Exception as e:
                log.exception('Calling TuShare too fast. Will sleep 1 minutes...', exc_info=e)
                time.sleep(60)
                ts_client.init_token()

        if stock_data is not None and not stock_data.empty:
            db_client.store_dataframe(stock_data, table.__tablename__)
            if from_date_to_ret is None:
                from_date_to_ret = from_date
            log.info('Successfully save %s of stock %s %s~%s' % (table.__tablename__, ts_code, from_date, next_date))

        from_date = date_utils.format_delta(next_date, 1)

    return True, from_date_to_ret


def fetch_period_report(ts_code: dict(type=str, help='股票编码'),
                        to_date: dict(type=str, help='数据要获取到哪天'),
                        to_do: dict(type=bool, help='是否要进行此次获取') = True):
    """
    按股票拉取季报相关的数据
    任何一步失败都可以退出
    """
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


def fetch_data_by_code(ts_code: str, to_date: str = date_utils.get_current_dt()):
    """
    按股票拉取所有需要的数据
    任何一步失败都可以退出
    :param ts_code: 股票编码
    :param to_date: 数据要获取到哪天
    """
    if to_date is None:
        to_date = date_utils.get_current_dt()
    # https://tushare.pro/document/2?doc_id=32 每日指标
    r, d1 = common_fetch_data(ts_code, 'fetch_daily_basic', TsDailyBasic,
                              TsDailyBasic.trade_date, TsDailyBasic.ts_code,
                              to_date=to_date, to_do=True)
    # https://tushare.pro/document/2?doc_id=27 日线行情
    r, d2 = common_fetch_data(ts_code, 'fetch_daily_bar', TsDailyTradeInfo,
                              TsDailyTradeInfo.trade_date, TsDailyTradeInfo.ts_code,
                              to_date=to_date, to_do=r)
    # https://tushare.pro/document/2?doc_id=28 复权因子
    r, d3 = common_fetch_data(ts_code, 'fetch_adj_factor', TsAdjFactor,
                              TsAdjFactor.trade_date, TsAdjFactor.ts_code,
                              to_date=to_date, to_do=r)
    # 季报等
    r, d4 = fetch_period_report(ts_code, to_date, to_do=r)

    # https://tushare.pro/document/2?doc_id=45 预报
    r, d5 = common_fetch_data(ts_code, 'fetch_forecast', TsForecast,
                              TsForecast.ann_date, TsForecast.ts_code,
                              to_date=to_date, to_do=r)
    # https://tushare.pro/document/2?doc_id=46 快报
    r, d6 = common_fetch_data(ts_code, 'fetch_express', TsExpress,
                              TsExpress.ann_date, TsExpress.ts_code,
                              to_date=to_date, to_do=r)
    # https://tushare.pro/document/2?doc_id=183
    r, d7 = common_fetch_data(ts_code, 'fetch_stk_limit', TsStkLimit,
                              TsStkLimit.trade_date, TsStkLimit.ts_code,
                              to_date=to_date, to_do=r)
    return r, compare_utils.mini(d1, d2, d3, d4, d5, d6, d7)
