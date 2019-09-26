#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" To fetch basic data from TuShare """
from sqlalchemy import and_
from sqlalchemy.orm import Session

import moquant.log as log
from moquant.constants import basic_start_date
from moquant.dbclient import db_client
from moquant.dbclient.mq_stock_mark import MqStockMark
from moquant.dbclient.ts_adj_factor import AdjFactor
from moquant.dbclient.ts_basic import StockBasic
from moquant.dbclient.ts_daily_trade_info import StockDailyInfo
from moquant.dbclient.ts_income import StockIncome
from moquant.tsclient import ts_client
from moquant.utils.datetime import format_delta, get_current_dt
from moquant.utils.env_utils import pass_fetch_basic


def fetch_from_date(table: str, date_field: str, ts_code: str):
    sql = 'select max(%s) as max_date from %s where ts_code=\'%s\'' % (date_field, table, ts_code)
    max_date = db_client.execute_sql(sql).fetchone()['max_date']
    from_date = basic_start_date
    if not (max_date is None):
        from_date = format_delta(max_date, day_num=1)
    return from_date


def common_fetch_data(ts_code: str, api_name: str, table_name: str, date_field: str):
    now_date = get_current_dt()
    from_date = fetch_from_date(table_name, date_field, ts_code)
    while True:
        to_date = format_delta(from_date, day_num=1000)

        if from_date > now_date:
            break

        log.info('To fetch %s of stock %s %s~%s' % (api_name, ts_code, from_date, to_date))
        stock_data = ts_client.fetch_data_frame(api_name, ts_code, to_date, from_date)

        if not stock_data.empty:
            db_client.store_dataframe(stock_data, table_name)
            print('Successfully save %s of stock %s %s~%s' % (api_name, ts_code, from_date, to_date))

        from_date = format_delta(to_date, day_num=1)


def fetch_data_by_code(stock_code):
    common_fetch_data(stock_code, 'fetch_daily_bar', StockDailyInfo.__tablename__, 'trade_date')
    common_fetch_data(stock_code, 'fetch_income', StockIncome.__tablename__, 'f_ann_date')
    common_fetch_data(stock_code, 'fetch_adj_factor', AdjFactor.__tablename__, 'trade_date')


def fetch_data():
    session: Session = db_client.get_session()
    result = session.query(MqStockMark).filter(
        and_(MqStockMark.fetch_data == 1, MqStockMark.last_handle_date < get_current_dt())).all()
    log.info(len(result))
    for row in result:
        fetch_data_by_code(row.ts_code)
        row.last_handle_date = get_current_dt()
        session.flush()


def init_stock_basic():
    if pass_fetch_basic():
        return

    # refresh stock basic every day, to update info and insert new stock
    session: Session = db_client.get_session()
    session.query(StockBasic).delete()

    stock_data = ts_client.fetch_all_stock()

    if not stock_data.empty:
        db_client.store_dataframe(stock_data, StockBasic.__tablename__)
        pass

    msm_list = session.query(MqStockMark).all()
    existed = [msm.ts_code for msm in msm_list]
    to_add_code = stock_data[~stock_data['ts_code'].isin(existed)]['ts_code'].array

    to_add_obj = [MqStockMark(ts_code=code, fetch_data=True, last_handle_date=basic_start_date) for code in to_add_code]

    if len(to_add_obj) > 0:
        session.add_all(to_add_obj)
        session.flush()


if __name__ == '__main__':
    init_stock_basic()
    fetch_data()
