#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" To fetch basic data from TuShare """

from pandas import DataFrame

import moquant.log as log
from moquant.dbclient import db_client
from moquant.dbclient.mq_stock_mark import MqStockMark
from moquant.dbclient.ts_adj_factor import AdjFactor
from moquant.tsclient import TsClient
from moquant.utils.datetime import format_delta, get_current_dt


def fetch_from_date(table: str, date_field: str, ts_code: str):
    sql = 'select max(%s) as max_date from %s where ts_code=\'%s\'' % (date_field, table, ts_code)
    max_date = db_client.execute_sql(sql).fetchone()['max_date']
    from_date = '19910101'
    if not (max_date is None):
        from_date = format_delta(max_date, day_num=1)
    return from_date


def fetch_daily_info(stock_code):
    ts = TsClient()

    now_date = get_current_dt()
    from_date = fetch_from_date('ts_daily_trade_info', 'trade_date', stock_code)
    while True:
        to_date = format_delta(from_date, day_num=1000)

        if from_date > now_date:
            break

        log.info('To fetch daily info of stock %s %s~%s' % (stock_code, from_date, to_date))
        try:
            stock_daily = ts.fetch_daily_bar(stock_code, to_date, from_date)
        except IOError:
            log.info('No daily info of stock %s %s~%s' % (stock_code, from_date, to_date))
            break

        if not stock_daily.empty:
            db_client.store_dataframe(stock_daily, 'ts_daily_trade_info')
            print('Successfully save daily info of stock %s %s~%s' % (stock_code, from_date, to_date))

        from_date = format_delta(to_date, day_num=1)


def fetch_income(stock_code):
    ts = TsClient()

    now_date = get_current_dt()
    from_date = fetch_from_date('ts_income', 'f_ann_date', stock_code)
    while True:
        to_date = format_delta(from_date, day_num=1000)
        if from_date > now_date:
            break

        log.info('To fetch income of stock %s %s~%s' % (stock_code, from_date, to_date))
        stock_income = ts.fetch_income(stock_code, to_date, from_date)  # type: DataFrame

        if not stock_income.empty:
            db_client.store_dataframe(stock_income, 'ts_income')
            print('Successfully save income of stock %s %s~%s' % (stock_code, from_date, to_date))

        from_date = format_delta(to_date, day_num=1)


def fetch_adj_factor(ts_code):
    ts = TsClient()

    now_date = get_current_dt()
    from_date = fetch_from_date(AdjFactor.__tablename__, 'ts_code', ts_code)
    while True:
        to_date = format_delta(from_date, day_num=1000)
        if from_date > now_date:
            break

        log.info('To fetch adj factor of stock %s %s~%s' % (ts_code, from_date, to_date))
        adj_factor = ts.fetch_adj_factor(ts_code, to_date, from_date)  # type: DataFrame

        if not adj_factor.empty:
            db_client.store_dataframe(adj_factor, AdjFactor.__tablename__)
            print('Successfully save adj factor of stock %s %s~%s' % (ts_code, from_date, to_date))

        from_date = format_delta(to_date, day_num=1)


def fetch_data_by_code(stock_code):
    fetch_daily_info(stock_code)
    fetch_income(stock_code)
    fetch_adj_factor(stock_code)


def fetch_data():
    session = db_client.get_session()
    result = session.query(MqStockMark).filter(MqStockMark.fetch_data == 1)
    for row in result:
        fetch_data_by_code(row.ts_code)


if __name__ == '__main__':
    fetch_data()
