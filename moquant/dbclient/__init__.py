#!/usr/bin/env python3
# -*- coding: utf-8 -*-
' DB Client '
__author__ = 'Momojie'

import moquant.log as log
import json as json
from sqlalchemy import create_engine


class DBClient(object):

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_inst'):
            cls._inst = super(DBClient, cls).__new__(cls, *args, **kwargs)
        return cls._inst

    def __init__(self):
        info_file = open('./resources/db_info.json', encoding='utf-8')
        info_json = json.load(info_file)
        log.info('数据库配置: %s' % json.dumps(info_json))
        self._engine = create_engine('mysql://%s:%s@%s:%d/%s' % (info_json['user'], info_json['password'], info_json['host'], info_json['port'], info_json['database']))

    def get_engine(self):
        return self._engine

    def store_dataframe(self, df, table, exists='append'):
        df.to_sql(table, self._engine, if_exists=exists, index=False)

    def execute_sql(self, sql):
        con = self._engine.connect()
        return con.execute(sql)
