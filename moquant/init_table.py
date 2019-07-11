#!/usr/bin/env python3
# -*- coding: utf-8 -*-
' To init table, will not create if table exists '
__author__ = 'Momojie'

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, DECIMAL, Index, Boolean
import moquant.dbclient as client


def create_table():
    engine = client.DBClient().get_engine()
    metadata = MetaData()
    daily_info_table(metadata)
    mq_stock_mark(metadata)

    metadata.create_all(engine)


def daily_info_table(metadata):
    Table('stock_daily_trade_info', metadata,
          Column('ts_code', String(10), primary_key=True),
          Column('trade_date', String(10), primary_key=True),
          Column('open', DECIMAL(10, 2)),
          Column('high', DECIMAL(10, 2)),
          Column('low', DECIMAL(10, 2)),
          Column('close', DECIMAL(10, 2)),
          Column('pre_close', DECIMAL(10, 2)),
          Column('change', DECIMAL(10, 2)),
          Column('pct_chg', DECIMAL(10, 2)),
          Column('vol', DECIMAL(10, 2)),
          Column('amount', DECIMAL(10, 2))
          )


def mq_stock_mark(metadata):
    Table('mq_stock_mark', metadata,
          Column('ts_code', String(10), primary_key=True),
          Column('fetch_data', Boolean, default=False)
          )


if __name__ == '__main__':
    create_table()
