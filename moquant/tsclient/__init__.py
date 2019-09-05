#!/usr/bin/env python3
# -*- coding: utf-8 -*-
' Interact with tushare '
__author__ = 'Momojie'


import json as json
import tushare as ts

import moquant.log as log


class TsClient(object):

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_inst'):
            cls._inst = super(TsClient, cls).__new__(cls, *args, **kwargs)
            cls._inst._ts = ts
            info_file = open('./resources/ts.json', encoding='utf-8')
            info_json = json.load(info_file)
            cls._inst._ts.set_token(info_json['token'])
            log.info('Init tushare token successfully')
            cls._inst._pro = cls._inst._ts.pro_api()
        return cls._inst

    # 每分钟200次
    def fetch_daily_bar(self, ts_code: str, end_date: str, start_date: str='19910101'):
        return self._ts.pro_bar(ts_code=ts_code, start_date=start_date, end_date=end_date, adj='qfq')

    def fetch_income(self, ts_code: str, end_date: str, start_date: str='19910101'):
        return self._pro.income(ts_code=ts_code, start_date=start_date, end_date=end_date)
