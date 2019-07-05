#!/usr/bin/env python3
# -*- coding: utf-8 -*-
' To fetch basic data from tushare '
__author__ = 'Momojie'

import datetime
import moquant.tsclient as ts
import moquant.log as log
from moquant.dbclient import DBClient
from moquant.dbclient.stock_daily_info import StockDailyInfo


def fetch_data_by_code(stock_code):
    ts.init_token()
    client = DBClient()

    while True:
        max_date = client.execute_sql('select max(trade_date) as max_date from stock_daily_trade_info where ts_code=\'%s\'' % stock_code).fetchone()['max_date']
        from_date = '20000101'
        if not (max_date is None):
            max_date_time = datetime.datetime.strptime(max_date, '%Y%m%d') + datetime.timedelta(days=1)
            from_date = datetime.datetime.strftime(max_date_time, "%Y%m%d")
        to_date = datetime.datetime.strftime(datetime.datetime.strptime(from_date, '%Y%m%d') + datetime.timedelta(days=1000), "%Y%m%d")
        now_date = datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%d")

        log.info('To fetch daily info of stock %s %s~%s' % (stock_code, from_date, to_date))
        stock_daily = ts.fetch_daily_bar(stock_code, to_date, from_date)
        #print(stock_daily)

        if not stock_daily.empty:
            client.store_dataframe(stock_daily, 'stock_daily_trade_info')
            print('Successfully save daily info of stock %s %s~%s' % (stock_code, from_date, to_date))

        if to_date >= now_date:
            break


def try_query():
    client = DBClient()
    session = client.get_session()
    result = session.query(StockDailyInfo).filter_by(StockDailyInfo.ts_code == '000001.SZ')
    log.info(result)


if __name__ == '__main__':
    #fetch_data_by_code('000001.SZ')
    try_query()

