#!/usr/bin/env python3
# -*- coding: utf-8 -*-
' Interact with tushare '
__author__ = 'Momojie'

import tushare as ts


def init_token():
    ts.set_token('8c94f3f4e1ed2199b3b48e0e3c2b164bcdc5744af3ba66a405c63202')


# 每分钟200次
def fetch_daily_bar(ts_code, end_date, start_date='20000101'):
    return ts.pro_bar(ts_code, start_date=start_date, end_date=end_date, adj='qfq')
