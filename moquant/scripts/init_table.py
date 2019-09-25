#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" To init table, will not create if table exists """

import moquant.dbclient as client
import moquant.dbclient.mq_stock_mark as mark
import moquant.dbclient.ts_adj_factor as adj_factory
import moquant.dbclient.ts_daily_trade_info as daily
import moquant.dbclient.ts_income as income


def create_table():
    engine = client.db_client.get_engine()

    # tushare
    daily.create(engine)
    income.create(engine)
    adj_factory.create(engine)

    #moquant
    mark.create(engine)


if __name__ == '__main__':
    create_table()
