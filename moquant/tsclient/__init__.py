#!/usr/bin/env python3
# -*- coding: utf-8 -*-
' Interact with tushare '
__author__ = 'Momojie'


import json as json
import tushare as ts

import moquant.log as log

from tushare.pro.client import DataApi


class TsClient(object):

    __ts: ts = None
    __pro: DataApi = None

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '__inst'):
            cls.__inst = super(TsClient, cls).__new__(cls, *args, **kwargs)
            cls.__inst.__ts = ts
            info_file = open('./resources/ts.json', encoding='utf-8')
            info_json = json.load(info_file)
            cls.__inst.__ts.set_token(info_json['token'])
            log.info('Init tushare token successfully')
            cls.__inst.__pro = cls.__inst.__ts.pro_api()
        return cls.__inst

    # 每分钟200次
    def fetch_daily_bar(self, ts_code: str, end_date: str, start_date: str = '19910101'):
        return self.__ts.pro_bar(ts_code=ts_code, start_date=start_date, end_date=end_date, adj='qfq')

    def fetch_income(self, ts_code: str, end_date: str, start_date: str = '19910101'):
        return self.__pro.income(ts_code=ts_code, start_date=start_date, end_date=end_date)
