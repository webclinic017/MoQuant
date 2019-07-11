#!/usr/bin/env python3
# -*- coding: utf-8 -*-
' DB Client '
__author__ = 'Momojie'

import moquant.log as log
import json as json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class DBClient(object):

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_inst'):
            cls._inst = super(DBClient, cls).__new__(cls, *args, **kwargs)
            info_file = open('./resources/db_info.json', encoding='utf-8')
            info_json = json.load(info_file)
            log.info('Database config: %s' % json.dumps(info_json))
            cls._inst._engine = create_engine('mysql://%s:%s@%s:%d/%s' % (info_json['user'], info_json['password'], info_json['host'], info_json['port'], info_json['database']))
            session = sessionmaker(bind=cls._inst._engine)
            cls._inst._session = session()
        return cls._inst

    def get_engine(self):
        return self._engine

    def store_dataframe(self, df, table, exists='append'):
        df.to_sql(table, self._engine, if_exists=exists, index=False)

    def execute_sql(self, sql):
        con = self._engine.connect()
        return con.execute(sql)

    def get_session(self):
        return self._session
