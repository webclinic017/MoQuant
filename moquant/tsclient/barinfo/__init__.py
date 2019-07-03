#!/usr/bin/env python3
# -*- coding: utf-8 -*-
' Interact with tushare , bar info only '
__author__ = 'Momojie'


import tushare as ts


# 每分钟200次
def fetch_daily_bar(ts_code, end_date, start_date='20000101'):
    return ts.pro_bar(ts_code, start_date=start_date, end_date=end_date, adj='qfq')
