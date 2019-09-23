#!/usr/bin/env python3
# -*- coding: utf-8 -*-
' To fetch basic data from tushare '
__author__ = 'Momojie'

import datetime

import moquant.log as log
from moquant.dbclient import DBClient
from moquant.dbclient.mq_stock_mark import MqStockMark
from moquant.tsclient import TsClient
from pandas import DataFrame


basic_start_date = '19910101'


def fetch_daily_info(stock_code):
    ts = TsClient()
    client = DBClient()

    while True:
        max_date = client.execute_sql('select max(trade_date) as max_date from tu_stock_daily_trade_info where ts_code=\'%s\'' % stock_code).fetchone()['max_date']
        from_date = basic_start_date
        if not (max_date is None):
            max_date_time = datetime.datetime.strptime(max_date, '%Y%m%d') + datetime.timedelta(days=1)
            from_date = datetime.datetime.strftime(max_date_time, "%Y%m%d")
        to_date = datetime.datetime.strftime(datetime.datetime.strptime(from_date, '%Y%m%d') + datetime.timedelta(days=1000), "%Y%m%d")
        now_date = datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%d")

        if from_date > now_date:
            break

        log.info('To fetch daily info of stock %s %s~%s' % (stock_code, from_date, to_date))
        try:
            stock_daily = ts.fetch_daily_bar(stock_code, to_date, from_date)
        except IOError:
            log.info('No daily info of stock %s %s~%s' % (stock_code, from_date, to_date))
            break

        if not stock_daily.empty:
            client.store_dataframe(stock_daily, 'tu_stock_daily_trade_info')
            print('Successfully save daily info of stock %s %s~%s' % (stock_code, from_date, to_date))

        if to_date >= now_date:
            break


def fetch_income(stock_code):
    ts = TsClient()
    client = DBClient()

    while True:
        max_date = client.execute_sql('select max(f_ann_date) as max_date from tu_stock_income where ts_code=\'%s\'' % stock_code).fetchone()['max_date']
        from_date = basic_start_date
        if not (max_date is None):
            max_date_time = datetime.datetime.strptime(max_date, '%Y%m%d') + datetime.timedelta(days=1)
            from_date = datetime.datetime.strftime(max_date_time, "%Y%m%d")
        to_date = datetime.datetime.strftime(datetime.datetime.strptime(from_date, '%Y%m%d') + datetime.timedelta(days=1000), "%Y%m%d")
        now_date = datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%d")

        if from_date > now_date:
            break

        log.info('To fetch income of stock %s %s~%s' % (stock_code, from_date, to_date))
        stock_income = ts.fetch_income(stock_code, to_date, from_date)  # type: DataFrame

        if not stock_income.empty:
            client.store_dataframe(stock_income, 'tu_stock_income')
            print('Successfully save income of stock %s %s~%s' % (stock_code, from_date, to_date))

        if to_date >= now_date:
            break


def fetch_data_by_code(stock_code):
    fetch_daily_info(stock_code)
    fetch_income(stock_code)


def fetch_data():
    client = DBClient()
    session = client.get_session()
    result = session.query(MqStockMark).filter(MqStockMark.fetch_data == 1)
    for row in result:
        fetch_data_by_code(row.ts_code)


if __name__ == '__main__':
    fetch_data()

