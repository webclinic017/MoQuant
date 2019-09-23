#!/usr/bin/env python3
# -*- coding: utf-8 -*-
' DB Client '
__author__ = 'Momojie'

import json as json

import pymysql
import sqlalchemy.engine.url as url
from pandas import DataFrame
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import moquant.log as log


class DBClient(object):

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_inst'):
            pymysql.install_as_MySQLdb()
            cls._inst = super(DBClient, cls).__new__(cls, *args, **kwargs)
            info_file = open('./resources/db_info.json', encoding='utf-8')
            info_json = json.load(info_file)
            engine_url = url.URL(
                drivername='mysql',
                host=info_json['host'],
                port=info_json['port'],
                username=info_json['user'],
                password=info_json['password'],
                database=info_json['database'],
                query={'charset': 'utf8'}
            )
            log.info('Database config: %s' % json.dumps(info_json))
            cls._inst._engine = create_engine(engine_url, encoding='utf-8')
            session = sessionmaker(bind=cls._inst._engine)
            cls._inst._session = session()
        return cls._inst

    def get_engine(self):
        return self._engine

    def store_dataframe(self, df: DataFrame, table: str, exists: str='append'):
        df.to_sql(table, self._engine, if_exists=exists, index=False, method='multi')

    def execute_sql(self, sql: str):
        con = self._engine.connect()
        return con.execute(sql)

    def get_session(self):
        return self._session
